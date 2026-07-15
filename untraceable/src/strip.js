// strip.js — the core. Pure functions, no DOM, no dependencies.
// Loaded as a plain <script> (not a module) so the exact same file runs inside
// the extension AND when tool.html is opened directly from disk (file://).
// Everything is attached to the global `MS` namespace.
//
// STRATEGY (read this once and you understand the whole product):
// An image file is a container of segments. Some segments draw the picture; the
// rest are metadata *about* it (who, where, when, with what). We use an
// ALLOW-LIST: keep ONLY the segments needed to draw the picture faithfully
// (image data + colour profile), and drop EVERYTHING else — known or unknown,
// compressed or not, in any order. A deny-list ("remove the blocks I know
// about") can never be proven complete, because containers permit arbitrary,
// duplicated, and custom segments. An allow-list is complete by construction:
// a leak-carrier that isn't on the keep-list is simply never copied.
//
// We never touch the compressed pixel bytes, so the picture is byte-for-byte
// identical — a lossless surgery, not a re-encode. Supported containers:
// JPEG/JFIF, PNG, WebP (RIFF). Anything else throws; the UI decides whether to
// offer the canvas re-encode fallback.
(function () {
  'use strict';
  const MS = (globalThis.MS = globalThis.MS || {});

  // ---- little byte helpers ----
  const u32be = (b, i) => ((b[i] << 24) | (b[i + 1] << 16) | (b[i + 2] << 8) | b[i + 3]) >>> 0;
  const u32le = (b, i) => (b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24)) >>> 0;
  const ascii = (b, i, n) => { let s = ''; for (let k = 0; k < n; k++) s += String.fromCharCode(b[i + k]); return s; };
  function startsWith(b, i, str) {
    if (i + str.length > b.length) return false;
    for (let k = 0; k < str.length; k++) if (b[i + k] !== str.charCodeAt(k)) return false;
    return true;
  }
  function concat(chunks) {
    let total = 0; for (const c of chunks) total += c.length;
    const out = new Uint8Array(total);
    let o = 0; for (const c of chunks) { out.set(c, o); o += c.length; }
    return out;
  }

  // ---- format detection (by magic bytes, never by file extension) ----
  function detectFormat(b) {
    if (b.length >= 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return 'jpeg';
    if (b.length >= 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47 &&
        b[4] === 0x0d && b[5] === 0x0a && b[6] === 0x1a && b[7] === 0x0a) return 'png';
    if (b.length >= 12 && ascii(b, 0, 4) === 'RIFF' && ascii(b, 8, 4) === 'WEBP') return 'webp';
    if (b.length >= 12 && (ascii(b, 4, 8) === 'ftypheic' || ascii(b, 4, 8) === 'ftypheix' ||
        ascii(b, 4, 8) === 'ftypmif1' || ascii(b, 4, 8) === 'ftyphevc')) return 'heic';
    if (b.length >= 12 && ascii(b, 4, 4) === 'ftyp' && ascii(b, 8, 4) === 'avif') return 'avif';
    if (b.length >= 3 && ascii(b, 0, 3) === 'GIF') return 'gif';
    if (b.length >= 2 && b[0] === 0x42 && b[1] === 0x4d) return 'bmp';
    if (b.length >= 4 && (u32le(b, 0) === 0x002a4949 || u32be(b, 0) === 0x4d4d002a)) return 'tiff';
    return 'unknown';
  }

  // ---------------------------------------------------------------------------
  // JPEG
  // ---------------------------------------------------------------------------
  // Walk marker by marker. Keep structural markers (tables, frame header, scan
  // data) plus the two colour-fidelity markers (ICC in APP2, Adobe transform in
  // APP14). Drop every APPn/COM that isn't one of those. The JFIF APP0 is
  // rebuilt to a clean 16-byte header so any inline JFIF thumbnail is discarded.
  // We stop at the first EOI, which also discards any trailing MPF/MPO images
  // (each a whole second copy of the scene with its own GPS).
  function rebuildJfifApp0(b, p, payloadLen) {
    // payload: "JFIF\0"(5) ver(2) units(1) Xden(2) Yden(2) Xthumb(1) Ythumb(1) [thumb…]
    if (payloadLen < 14) return { bytes: b.subarray(p - 4, p + payloadLen), hadThumb: false };
    const seg = new Uint8Array(18);         // FFE0 + len(2) + 14 payload
    seg[0] = 0xff; seg[1] = 0xe0; seg[2] = 0x00; seg[3] = 0x10; // length = 16
    seg.set(b.subarray(p, p + 12), 4);      // "JFIF\0" ver units Xden Yden
    seg[16] = 0; seg[17] = 0;               // Xthumbnail = Ythumbnail = 0
    return { bytes: seg, hadThumb: payloadLen > 14 };
  }

  function classifyJpegApp(marker, b, p, len) {
    // p = payload start, len = payload length (excludes the 2 length bytes)
    if (marker === 0xe0) {
      if (startsWith(b, p, 'JFIF\0')) return { action: 'rebuildJfif' };
      if (startsWith(b, p, 'JFXX\0')) return { action: 'drop', label: 'JFIF extension thumbnail', kind: 'thumbnail' };
      return { action: 'drop', label: 'APP0 data', kind: 'other' };
    }
    if (marker === 0xe1) {
      if (startsWith(b, p, 'Exif\0')) return { action: 'drop', label: 'EXIF (camera, GPS, timestamps, thumbnail)', kind: 'exif' };
      if (startsWith(b, p, 'http://ns.adobe.com/xap/1.0/\0')) return { action: 'drop', label: 'XMP metadata', kind: 'xmp' };
      if (startsWith(b, p, 'http://ns.adobe.com/xmp/extension/')) return { action: 'drop', label: 'Extended XMP', kind: 'xmp' };
      return { action: 'drop', label: 'APP1 metadata', kind: 'other' };
    }
    if (marker === 0xe2) {
      if (startsWith(b, p, 'ICC_PROFILE\0')) return { action: 'keep' };            // colour fidelity
      if (startsWith(b, p, 'MPF\0')) return { action: 'drop', label: 'Multi-Picture (extra embedded images)', kind: 'other' };
      return { action: 'drop', label: 'APP2 data', kind: 'other' };
    }
    if (marker === 0xed) {
      if (startsWith(b, p, 'Photoshop 3.0\0')) return { action: 'drop', label: 'IPTC / Photoshop (captions, byline, keywords)', kind: 'iptc' };
      return { action: 'drop', label: 'APP13 data', kind: 'other' };
    }
    if (marker === 0xee) {                                                          // APP14 "Adobe" colour transform
      if (startsWith(b, p, 'Adobe')) return { action: 'keep' };
      return { action: 'drop', label: 'APP14 data', kind: 'other' };
    }
    if (marker === 0xeb) return { action: 'drop', label: 'JUMBF / Content Credentials (C2PA)', kind: 'other' }; // APP11
    if (marker === 0xfe) return { action: 'drop', label: 'Comment', kind: 'comment' };                          // COM
    if (marker >= 0xe0 && marker <= 0xef) return { action: 'drop', label: 'APP' + (marker - 0xe0) + ' metadata', kind: 'other' };
    return { action: 'keep' };                                                      // tables / frame headers
  }

  function stripJpeg(b) {
    if (b.length < 2 || b[0] !== 0xff || b[1] !== 0xd8) throw new Error('Not a JPEG (missing start marker).');
    const kept = [b.subarray(0, 2)];       // SOI
    const removed = [];
    let i = 2;
    while (i < b.length) {
      if (b[i] !== 0xff) throw new Error('Malformed JPEG: expected a marker at byte ' + i + '.');
      let marker = b[i + 1];
      while (marker === 0xff && i + 2 < b.length) { i++; marker = b[i + 1]; }        // skip fill bytes
      if (marker === 0xd9) {                                                         // EOI — stop, drop any trailer
        kept.push(b.subarray(i, i + 2)); i += 2;
        if (i < b.length) removed.push({ label: 'Trailing data after image (e.g. appended video/file)', kind: 'trailer', bytes: b.length - i });
        break;
      }
      if ((marker >= 0xd0 && marker <= 0xd7) || marker === 0x01) { kept.push(b.subarray(i, i + 2)); i += 2; continue; }
      if (marker === 0xda) {                                                          // SOS + entropy scan
        const start = i;
        if (i + 4 > b.length) throw new Error('Malformed JPEG: truncated scan header.');
        const len = (b[i + 2] << 8) | b[i + 3];
        let j = i + 2 + len;
        while (j < b.length - 1) {
          if (b[j] === 0xff) {
            const m = b[j + 1];
            if (m === 0x00) { j += 2; continue; }
            if (m >= 0xd0 && m <= 0xd7) { j += 2; continue; }
            if (m === 0xff) { j += 1; continue; }
            break;
          }
          j++;
        }
        if (j >= b.length - 1) j = b.length;
        kept.push(b.subarray(start, j));
        i = j;
        continue;
      }
      if (i + 4 > b.length) throw new Error('Malformed JPEG: truncated segment.');
      const len = (b[i + 2] << 8) | b[i + 3];
      if (len < 2) throw new Error('Malformed JPEG: bad segment length.');
      const end = i + 2 + len;
      if (end > b.length) throw new Error('Malformed JPEG: segment runs past end of file.');
      const d = classifyJpegApp(marker, b, i + 4, len - 2);
      if (d.action === 'keep') kept.push(b.subarray(i, end));
      else if (d.action === 'rebuildJfif') {
        const r = rebuildJfifApp0(b, i + 4, len - 2);
        kept.push(r.bytes);
        if (r.hadThumb) removed.push({ label: 'JFIF thumbnail', kind: 'thumbnail', bytes: (len - 2) - 14 });
      } else removed.push({ label: d.label, kind: d.kind, bytes: end - i });
      i = end;
    }
    return { format: 'jpeg', method: 'lossless', output: concat(kept), removed, changed: removed.length > 0 };
  }

  // ---------------------------------------------------------------------------
  // PNG — allow-list of render + colour chunks; everything else dropped.
  // ---------------------------------------------------------------------------
  const PNG_KEEP = new Set([
    'IHDR', 'PLTE', 'IDAT', 'IEND', 'tRNS',                       // render-critical
    'gAMA', 'cHRM', 'sRGB', 'iCCP', 'sBIT', 'cICP', 'mDCV', 'cLLI', // colour
    'bKGD', 'pHYs', 'hIST',                                        // harmless rendering hints
    'acTL', 'fcTL', 'fdAT',                                        // APNG animation
  ]);
  const PNG_LABEL = {
    tEXt: 'Text metadata (author, software, comment…)',
    zTXt: 'Compressed text metadata',
    iTXt: 'International text / XMP metadata',
    eXIf: 'EXIF (camera, GPS)',
    tIME: 'Last-modified timestamp',
    dSIG: 'Digital signature',
    sPLT: 'Suggested-palette (named)',
  };
  function stripPng(b) {
    const sig = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
    for (let k = 0; k < 8; k++) if (b[k] !== sig[k]) throw new Error('Not a PNG (bad signature).');
    const kept = [b.subarray(0, 8)];
    const removed = [];
    let i = 8;
    while (i < b.length) {
      if (i + 8 > b.length) throw new Error('Malformed PNG: truncated chunk header.');
      const len = u32be(b, i);
      const type = ascii(b, i + 4, 4);
      const end = i + 12 + len;            // 4 length + 4 type + len data + 4 crc
      if (end > b.length) throw new Error('Malformed PNG: chunk runs past end of file.');
      if (PNG_KEEP.has(type)) kept.push(b.subarray(i, end));
      else removed.push({ label: PNG_LABEL[type] || (type + ' chunk'), kind: type === 'eXIf' ? 'exif' : 'text', bytes: end - i });
      i = end;
      if (type === 'IEND') break;
    }
    return { format: 'png', method: 'lossless', output: concat(kept), removed, changed: removed.length > 0 };
  }

  // ---------------------------------------------------------------------------
  // WebP (RIFF) — allow-list of render + colour chunks; drop EXIF/XMP/unknown
  // and clear the VP8X EXIF/XMP flag bits so the header matches reality.
  // ---------------------------------------------------------------------------
  const WEBP_KEEP = new Set(['VP8X', 'VP8 ', 'VP8L', 'ALPH', 'ANIM', 'ANMF', 'ICCP']);
  function stripWebp(b) {
    if (ascii(b, 0, 4) !== 'RIFF' || ascii(b, 8, 4) !== 'WEBP') throw new Error('Not a WebP (bad RIFF header).');
    const body = [];
    const removed = [];
    let vp8x = null;
    let i = 12;
    while (i + 8 <= b.length) {
      const fourcc = ascii(b, i, 4);
      const size = u32le(b, i + 4);
      const end = i + 8 + size + (size & 1);   // chunks are padded to even length
      if (end > b.length) throw new Error('Malformed WebP: chunk runs past end of file.');
      if (WEBP_KEEP.has(fourcc)) {
        if (fourcc === 'VP8X') { vp8x = b.slice(i, end); body.push(vp8x); }   // own copy to edit flags
        else body.push(b.subarray(i, end));
      } else {
        const label = fourcc === 'EXIF' ? 'EXIF (camera, GPS)' : fourcc === 'XMP ' ? 'XMP metadata' : (fourcc.trim() + ' chunk');
        removed.push({ label, kind: fourcc === 'EXIF' ? 'exif' : fourcc === 'XMP ' ? 'xmp' : 'other', bytes: end - i });
      }
      i = end;
    }
    const hadFlags = !!(vp8x && (vp8x[8] & 0x0c));   // was a stale EXIF/XMP flag actually set?
    if (vp8x) vp8x[8] &= ~0x0c;   // clear EXIF (0x08) + XMP (0x04) flag bits; keep ICC (0x20)
    if (hadFlags) removed.push({ label: 'Stale WebP EXIF/XMP header flags', kind: 'flags', bytes: 0 });
    const head = b.subarray(0, 12);
    const out = concat([head, ...body]);
    let riffSize = 4;             // the "WEBP" fourcc counts toward the RIFF size
    for (const c of body) riffSize += c.length;
    out[4] = riffSize & 0xff; out[5] = (riffSize >>> 8) & 0xff; out[6] = (riffSize >>> 16) & 0xff; out[7] = (riffSize >>> 24) & 0xff;
    return { format: 'webp', method: 'lossless', output: out, removed, changed: removed.length > 0 };
  }

  // ---- dispatch ----
  function stripBytes(b) {
    const fmt = detectFormat(b);
    if (fmt === 'jpeg') return stripJpeg(b);
    if (fmt === 'png') return stripPng(b);
    if (fmt === 'webp') return stripWebp(b);
    const known = { heic: 'HEIC/HEIF', avif: 'AVIF', gif: 'GIF', bmp: 'BMP', tiff: 'TIFF' };
    const name = known[fmt];
    const e = new Error(name ? name + ' is not supported — MetaStrip handles JPEG, PNG and WebP.'
                             : 'This file is not a JPEG, PNG or WebP image.');
    e.code = name ? 'UNSUPPORTED_FORMAT' : 'NOT_AN_IMAGE';
    e.format = fmt;
    throw e;
  }

  MS.SUPPORTED = ['jpeg', 'png', 'webp'];
  MS.detectFormat = detectFormat;
  MS.stripJpeg = stripJpeg;
  MS.stripPng = stripPng;
  MS.stripWebp = stripWebp;
  MS.stripBytes = stripBytes;
})();
