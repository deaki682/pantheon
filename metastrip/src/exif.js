// exif.js — the metadata *reader*. Pure functions, no DOM, no dependencies.
// Loaded as a plain <script>; attaches to the global `MS` namespace.
//
// Two jobs:
//   1. MS.readMetadataSummary(bytes) → a human-readable list of what a file leaks
//      (GPS, camera serial, timestamps, author, thumbnail…). Shown BEFORE
//      stripping — the proof, and the whole demo.
//   2. MS.verifyClean(bytes) → re-scan the stripped output and confirm nothing
//      identifying survived. Powers the "Verified clean" badge.
//
// It reads only the carriers a privacy tool cares about; it is not a full EXIF
// browser. If a block is malformed it degrades to "present (unreadable)" rather
// than throwing — a reader must never crash the batch.
(function () {
  'use strict';
  const MS = (globalThis.MS = globalThis.MS || {});
  const td = new TextDecoder('utf-8', { fatal: false });

  const ascii = (b, i, n) => { let s = ''; for (let k = 0; k < n && i + k < b.length; k++) s += String.fromCharCode(b[i + k]); return s; };
  function startsWith(b, i, str) {
    if (i + str.length > b.length) return false;
    for (let k = 0; k < str.length; k++) if (b[i + k] !== str.charCodeAt(k)) return false;
    return true;
  }

  // ---- shared TIFF/EXIF IFD parser (JPEG APP1, PNG eXIf, WebP EXIF) ----
  // Offsets are relative to the TIFF header start (the byte after "Exif\0\0").
  // Endianness comes from the II/MM byte-order mark. Values ≤4 bytes are inline;
  // larger ones are stored at an offset. GPS and the Exif sub-block hang off
  // pointer tags in IFD0; IFD1 (if present) is the embedded thumbnail.
  const TYPE_SIZE = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8 };
  const MAX_ELEMS = 4096; // cap per-entry element count so a hostile file can't wedge the tab
  const IFD0_NAMED = new Set([0x010e, 0x010f, 0x0110, 0x0131, 0x0132, 0x013b, 0x013c, 0x8298]);
  const EXIF_NAMED = new Set([0x9003, 0xa430, 0xa431, 0xa434, 0xa435]);
  const IFD_POINTERS = new Set([0x8769, 0x8825, 0xa005]);

  function parseExifTiff(b, start) {
    try {
      if (start < 0 || start + 8 > b.length) return null;
      const bo = (b[start] << 8) | b[start + 1];
      if (bo !== 0x4949 && bo !== 0x4d4d) return null;          // 'II' little / 'MM' big
      const le = bo === 0x4949;
      const dv = new DataView(b.buffer, b.byteOffset, b.length);
      const u16 = (a) => (a >= 0 && a + 2 <= b.length ? dv.getUint16(a, le) : 0);
      const u32 = (a) => (a >= 0 && a + 4 <= b.length ? dv.getUint32(a, le) : 0);
      const i32 = (a) => (a >= 0 && a + 4 <= b.length ? dv.getInt32(a, le) : 0);
      if (u16(start + 2) !== 0x002a) return null;

      const readIFD = (ifdAbs) => {
        const out = { entries: [], nextOff: 0 };
        if (ifdAbs < start || ifdAbs + 2 > b.length) return out;
        const count = u16(ifdAbs);
        if (count > 4096) return out;                          // sanity guard
        let p = ifdAbs + 2;
        for (let n = 0; n < count; n++, p += 12) {
          if (p + 12 > b.length) break;
          const tag = u16(p), type = u16(p + 2), cnt = u32(p + 4);
          const size = (TYPE_SIZE[type] || 1) * cnt;
          const valAbs = size <= 4 ? p + 8 : start + u32(p + 8);
          out.entries.push({ tag, type, cnt, size, valAbs });
        }
        out.nextOff = u32(ifdAbs + 2 + count * 12);
        return out;
      };
      const str = (e) => {
        if (e.valAbs < 0 || e.valAbs + e.size > b.length) return '';
        let s = '';
        const n = Math.min(e.size, MAX_ELEMS);
        for (let k = 0; k < n; k++) { const c = b[e.valAbs + k]; if (c === 0) break; s += String.fromCharCode(c); }
        return s.trim();
      };
      const nums = (e) => {
        const arr = []; const sz = TYPE_SIZE[e.type] || 1;
        const n = Math.min(e.cnt, MAX_ELEMS);          // hostile files can declare cnt up to 4G
        for (let k = 0; k < n; k++) {
          const o = e.valAbs + k * sz;
          if (o + sz > b.length) break;
          if (e.type === 3) arr.push(u16(o));
          else if (e.type === 4) arr.push(u32(o));
          else if (e.type === 5) arr.push([u32(o), u32(o + 4)]);
          else if (e.type === 9) arr.push(i32(o));
          else if (e.type === 10) arr.push([i32(o), i32(o + 4)]);
          else arr.push(b[o]);
        }
        return arr;
      };

      const fields = {};
      let gps = null, hasThumbnail = false, otherTags = 0, exifAbs = 0, gpsAbs = 0;

      // "otherTags" counts only the non-pointer, non-surfaced technical tags in
      // IFD0 and the Exif sub-IFD — NOT the pointer entries, and NOT the GPS or
      // thumbnail sub-entries (those are each already represented by one finding).
      const ifd0 = readIFD(start + u32(start + 4));
      for (const e of ifd0.entries) {
        if (!IFD0_NAMED.has(e.tag) && !IFD_POINTERS.has(e.tag)) otherTags++;
        switch (e.tag) {
          case 0x010e: fields.description = str(e); break;
          case 0x010f: fields.make = str(e); break;
          case 0x0110: fields.model = str(e); break;
          case 0x0131: fields.software = str(e); break;
          case 0x0132: fields.dateTime = str(e); break;
          case 0x013b: fields.artist = str(e); break;
          case 0x013c: fields.host = str(e); break;
          case 0x8298: fields.copyright = str(e); break;
          case 0x8769: exifAbs = start + u32(e.valAbs); break;   // Exif sub-IFD pointer
          case 0x8825: gpsAbs = start + u32(e.valAbs); break;    // GPS IFD pointer
        }
      }
      if (ifd0.nextOff) hasThumbnail = true;

      if (exifAbs) {
        const ex = readIFD(exifAbs);
        for (const e of ex.entries) {
          if (!EXIF_NAMED.has(e.tag) && !IFD_POINTERS.has(e.tag)) otherTags++;
          switch (e.tag) {
            case 0x9003: fields.dateTimeOriginal = str(e); break;
            case 0xa430: fields.owner = str(e); break;           // CameraOwnerName
            case 0xa431: fields.bodySerial = str(e); break;
            case 0xa434: fields.lensModel = str(e); break;
            case 0xa435: fields.lensSerial = str(e); break;
          }
        }
      }
      if (gpsAbs) gps = parseGps(readIFD(gpsAbs).entries, str, nums);
      return { fields, gps, hasThumbnail, otherTags };
    } catch { return null; }
  }

  function parseGps(entries, str, nums) {
    let latRef, lat, lonRef, lon, alt;
    for (const e of entries) {
      if (e.tag === 1) { if (latRef === undefined) latRef = str(e); }
      else if (e.tag === 2) { if (!lat) lat = nums(e); }
      else if (e.tag === 3) { if (lonRef === undefined) lonRef = str(e); }
      else if (e.tag === 4) { if (!lon) lon = nums(e); }
      else if (e.tag === 6) { if (!alt) alt = nums(e); }
      if (latRef !== undefined && lat && lonRef !== undefined && lon && alt) break; // stop after first full set
    }
    if (!lat || !lon || lat.length < 3 || lon.length < 3) return null;
    const rat = (x) => (Array.isArray(x) ? (x[1] ? x[0] / x[1] : 0) : 0);
    const toDeg = (dms, ref) => {
      let v = rat(dms[0]) + rat(dms[1]) / 60 + rat(dms[2]) / 3600;
      if (ref === 'S' || ref === 'W') v = -v;
      return v;
    };
    const latitude = toDeg(lat, latRef);
    const longitude = toDeg(lon, lonRef);
    if (!isFinite(latitude) || !isFinite(longitude)) return null;
    let altitude = null;
    if (alt && alt[0]) { const a = rat(alt[0]); altitude = isFinite(a) ? a : null; }
    return { latitude, longitude, altitude };
  }

  // ---- turn a parsed TIFF into human findings ----
  function collectExif(t, findings, flags) {
    const push = (o) => findings.push(o);
    if (t.gps) {
      flags.gps = t.gps;
      push({ label: 'GPS location', value: `${t.gps.latitude.toFixed(6)}, ${t.gps.longitude.toFixed(6)} — where the photo was taken`, severity: 'high' });
    }
    const when = t.fields.dateTimeOriginal || t.fields.dateTime;
    if (when) push({ label: 'Date & time taken', value: when, severity: 'med' });
    const cam = [t.fields.make, t.fields.model].filter(Boolean).join(' ');
    if (cam) push({ label: 'Camera / device', value: cam, severity: 'med' });
    if (t.fields.owner) push({ label: 'Camera owner', value: t.fields.owner, severity: 'high' });
    if (t.fields.bodySerial) push({ label: 'Camera serial number', value: t.fields.bodySerial, severity: 'high' });
    if (t.fields.lensModel) push({ label: 'Lens', value: t.fields.lensModel, severity: 'low' });
    if (t.fields.lensSerial) push({ label: 'Lens serial number', value: t.fields.lensSerial, severity: 'high' });
    if (t.fields.software) push({ label: 'Software', value: t.fields.software, severity: 'low' });
    if (t.fields.artist) push({ label: 'Author / artist', value: t.fields.artist, severity: 'high' });
    if (t.fields.host) push({ label: 'Host computer', value: t.fields.host, severity: 'med' });
    if (t.fields.description) push({ label: 'Image description', value: t.fields.description, severity: 'low' });
    if (t.fields.copyright) push({ label: 'Copyright', value: t.fields.copyright, severity: 'low' });
    if (t.hasThumbnail) { flags.thumbnail = true; push({ label: 'Embedded thumbnail', value: 'a small copy of the original — can retain the UN-edited image', severity: 'high' }); }
    if (t.otherTags > 0) push({ label: 'Other technical tags', value: `${t.otherTags} more camera settings (exposure, ISO, orientation…)`, severity: 'low' });
    flags.exif = true;
  }

  function collectXmp(b, start, len, findings, flags) {
    flags.xmp = true;
    let creator = '', gps = '';
    try {
      const xml = td.decode(b.subarray(start, start + Math.max(0, len)));
      const m1 = xml.match(/<dc:creator>[\s\S]*?<rdf:li[^>]*>([^<]+)<\/rdf:li>/) || xml.match(/photoshop:Author[^>]*>([^<]+)</);
      if (m1) creator = m1[1].trim();
      const glat = xml.match(/exif:GPSLatitude[>="]+([^<"]+)/);
      const glon = xml.match(/exif:GPSLongitude[>="]+([^<"]+)/);
      if (glat && glon) gps = `${glat[1]} , ${glon[1]}`;
    } catch { /* ignore */ }
    if (gps) findings.push({ label: 'GPS location (XMP)', value: gps, severity: 'high' });
    if (creator) findings.push({ label: 'Author / creator (XMP)', value: creator, severity: 'high' });
    findings.push({ label: 'XMP metadata', value: 'edit history, ratings, may include creator & GPS', severity: 'med' });
  }

  // ---- per-format readers ----
  function readJpeg(b) {
    const findings = [], flags = {};
    let i = 2;
    while (i < b.length) {
      if (b[i] !== 0xff) break;
      let marker = b[i + 1];
      while (marker === 0xff && i + 2 < b.length) { i++; marker = b[i + 1]; }
      if (marker === 0xd9 || marker === 0xda) break;             // EOI or start of scan
      if ((marker >= 0xd0 && marker <= 0xd7) || marker === 0x01) { i += 2; continue; }
      if (i + 4 > b.length) break;
      const len = (b[i + 2] << 8) | b[i + 3];
      const p = i + 4;
      if (marker === 0xe1) {
        if (startsWith(b, p, 'Exif\0')) {
          const t = parseExifTiff(b, p + 6);
          if (t) collectExif(t, findings, flags);
          else { flags.exif = true; findings.push({ label: 'EXIF metadata', value: 'present (unreadable) — will be removed', severity: 'high' }); }
        } else if (startsWith(b, p, 'http://ns.adobe.com/xap/1.0/\0')) {
          collectXmp(b, p + 29, len - 2 - 29, findings, flags);
        } else if (startsWith(b, p, 'http://ns.adobe.com/xmp/extension/')) {
          flags.xmp = true; findings.push({ label: 'Extended XMP', value: 'overflow metadata block', severity: 'med' });
        }
      } else if (marker === 0xed && startsWith(b, p, 'Photoshop 3.0\0')) {
        flags.iptc = true; findings.push({ label: 'IPTC / Photoshop data', value: 'captions, byline, keywords', severity: 'med' });
      } else if (marker === 0xfe) {
        flags.comment = true;
        const txt = td.decode(b.subarray(p, p + Math.min(len - 2, 120))).replace(/\0+$/, '').trim();
        findings.push({ label: 'Comment', value: txt || 'present', severity: 'low' });
      }
      i += 2 + len;
    }
    return { findings, flags };
  }

  function readPng(b) {
    const findings = [], flags = {};
    let i = 8;
    while (i + 8 <= b.length) {
      const len = ((b[i] << 24) | (b[i + 1] << 16) | (b[i + 2] << 8) | b[i + 3]) >>> 0;
      const type = ascii(b, i + 4, 4);
      const data = i + 8;
      const end = i + 12 + len;
      if (end > b.length) break;
      const limit = end - 4;                       // keyword/text NUL must be found inside the chunk, not the CRC or next chunk
      const nul = (from) => { const z = b.indexOf(0, from); return z < 0 || z > limit ? limit : z; };
      if (type === 'tEXt') {
        const z = nul(data);
        const key = ascii(b, data, z - data);
        const val = td.decode(b.subarray(Math.min(z + 1, limit), limit));
        flags.text = true;
        findings.push({ label: `Text: ${key || 'metadata'}`, value: val.slice(0, 120) || 'present', severity: /author|artist|copyright|comment|gps|location/i.test(key) ? 'med' : 'low' });
      } else if (type === 'zTXt') {
        const z = nul(data);
        const key = ascii(b, data, z - data);
        flags.text = true; findings.push({ label: `Compressed text: ${key || 'metadata'}`, value: 'present — will be removed', severity: 'low' });
      } else if (type === 'iTXt') {
        const z = nul(data);
        const key = ascii(b, data, z - data);
        const isXmp = /xmp/i.test(key);
        flags.text = true; if (isXmp) flags.xmp = true;
        findings.push({ label: isXmp ? 'XMP metadata' : `Text: ${key || 'metadata'}`, value: isXmp ? 'edit history, may include creator & GPS' : 'present', severity: isXmp ? 'med' : 'low' });
      } else if (type === 'eXIf') {
        const t = parseExifTiff(b, data);
        if (t) collectExif(t, findings, flags);
        else { flags.exif = true; findings.push({ label: 'EXIF metadata', value: 'present (unreadable) — will be removed', severity: 'high' }); }
      } else if (type === 'tIME') {
        flags.time = true;
        if (data + 7 <= b.length) {
          const y = (b[data] << 8) | b[data + 1];
          const s = `${y}-${String(b[data + 2]).padStart(2, '0')}-${String(b[data + 3]).padStart(2, '0')} ${String(b[data + 4]).padStart(2, '0')}:${String(b[data + 5]).padStart(2, '0')}`;
          findings.push({ label: 'Last-modified timestamp', value: s, severity: 'low' });
        } else findings.push({ label: 'Last-modified timestamp', value: 'present', severity: 'low' });
      }
      i = end;
      if (type === 'IEND') break;
    }
    return { findings, flags };
  }

  function readWebp(b) {
    const findings = [], flags = {};
    let i = 12;
    while (i + 8 <= b.length) {
      const fourcc = ascii(b, i, 4);
      const size = (b[i + 4] | (b[i + 5] << 8) | (b[i + 6] << 16) | (b[i + 7] << 24)) >>> 0;
      const data = i + 8;
      const end = data + size + (size & 1);
      if (end > b.length) break;
      if (fourcc === 'EXIF') {
        const off = startsWith(b, data, 'Exif\0') ? data + 6 : data;
        const t = parseExifTiff(b, off);
        if (t) collectExif(t, findings, flags);
        else { flags.exif = true; findings.push({ label: 'EXIF metadata', value: 'present (unreadable) — will be removed', severity: 'high' }); }
      } else if (fourcc === 'XMP ') {
        collectXmp(b, data, size, findings, flags);
      }
      i = end;
    }
    return { findings, flags };
  }

  function fmtOf(b) {
    if (b.length >= 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return 'jpeg';
    if (b.length >= 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return 'png';
    if (b.length >= 12 && ascii(b, 0, 4) === 'RIFF' && ascii(b, 8, 4) === 'WEBP') return 'webp';
    return 'unknown';
  }
  function readAny(b, fmt) {
    if (fmt === 'jpeg') return readJpeg(b);
    if (fmt === 'png') return readPng(b);
    if (fmt === 'webp') return readWebp(b);
    return { findings: [], flags: {} };
  }

  MS.readMetadataSummary = function (b) {
    const fmt = fmtOf(b);
    const { findings } = readAny(b, fmt);
    const rank = { high: 0, med: 1, low: 2 };
    findings.sort((a, c) => (rank[a.severity] ?? 3) - (rank[c.severity] ?? 3));
    return { format: fmt, findings, hasAny: findings.length > 0 };
  };
  MS.verifyClean = function (b) {
    const fmt = fmtOf(b);
    const { findings } = readAny(b, fmt);
    return { clean: findings.length === 0, remaining: findings.map((f) => f.label) };
  };
})();
