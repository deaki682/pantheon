// Node test harness for the pure core (strip.js / exif.js / zip.js).
// The core files are plain <script>s that attach to globalThis.MS, so we eval
// them into this process, then drive them with synthetic files whose metadata
// is known. Run: node tests/core.test.mjs
import fs from 'node:fs';
import zlib from 'node:zlib';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const f of ['strip.js', 'exif.js', 'zip.js']) {
  // eslint-disable-next-line no-eval
  (0, eval)(fs.readFileSync(path.join(ROOT, 'src', f), 'utf8'));
}
const MS = globalThis.MS;

let passed = 0, failed = 0;
const assert = (cond, msg) => { if (cond) { passed++; } else { failed++; console.error('  ✗ ' + msg); } };
const section = (n) => console.log('\n' + n);
const U8 = (arr) => Uint8Array.from(arr.flat(Infinity));
function contains(hay, needle) { // subsequence search in a Uint8Array
  const n = typeof needle === 'string' ? [...Buffer.from(needle, 'latin1')] : needle;
  outer: for (let i = 0; i <= hay.length - n.length; i++) { for (let j = 0; j < n.length; j++) if (hay[i + j] !== n[j]) continue outer; return true; }
  return false;
}
const LE16 = (v) => [v & 0xff, (v >> 8) & 0xff];
const LE32 = (v) => [v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, (v >> 24) & 0xff];
const BE16 = (v) => [(v >> 8) & 0xff, v & 0xff];
const BE32 = (v) => [(v >> 24) & 0xff, (v >> 16) & 0xff, (v >> 8) & 0xff, v & 0xff];

// CRC32 for building valid PNG chunks
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(bytes) { let c = 0xffffffff; for (let i = 0; i < bytes.length; i++) c = CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

// ---- shared: a little-endian EXIF TIFF with Make="Canon" + GPS 37°48'30"N 122°25'E ----
function exifTiff() {
  const makeStr = [...Buffer.from('Canon\0')];
  const entry = (tag, type, count, val) => [...LE16(tag), ...LE16(type), ...LE32(count), ...LE32(val)];
  const rat = (n, d) => [...LE32(n), ...LE32(d)];
  const makeOff = 38, gpsIfdOff = 44, latOff = 98, lonOff = 122;
  const header = [0x49, 0x49, 0x2a, 0x00, ...LE32(8)];
  const ifd0 = [...LE16(2), ...entry(0x010f, 2, 6, makeOff), ...entry(0x8825, 4, 1, gpsIfdOff), ...LE32(0)];
  const gpsIfd = [...LE16(4),
    ...entry(0x0001, 2, 2, 0x4e), ...entry(0x0002, 5, 3, latOff),
    ...entry(0x0003, 2, 2, 0x45), ...entry(0x0004, 5, 3, lonOff), ...LE32(0)];
  const latRat = [...rat(37, 1), ...rat(48, 1), ...rat(30, 1)];
  const lonRat = [...rat(122, 1), ...rat(25, 1), ...rat(0, 1)];
  return U8([header, ifd0, makeStr, gpsIfd, latRat, lonRat]);
}

// =====================================================================
section('JPEG');
{
  const tiff = exifTiff();
  const jfif = [0x4a, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0xaa, 0xbb, 0xcc]; // 1×1 thumb AABBCC
  const exif = [0x45, 0x78, 0x69, 0x66, 0x00, 0x00, ...tiff];
  const com = [...Buffer.from('hidden note')];
  const iptc = [...Buffer.from('Photoshop 3.0\0'), 0x38, 0x42, 0x49, 0x4d, 0, 0, 0, 0];
  const dqt = [0xff, 0xdb, ...BE16(4), 0x00, 0x01];
  const sof = [0xff, 0xc0, ...BE16(5), 0x08, 0x00, 0x01];
  const dht = [0xff, 0xc4, ...BE16(4), 0x00, 0x02];
  const sos = [0xff, 0xda, ...BE16(4), 0x01, 0x00, 0x11, 0x22, 0x33];
  const jpeg = U8([
    [0xff, 0xd8],
    [0xff, 0xe0, ...BE16(jfif.length + 2), ...jfif],
    [0xff, 0xe1, ...BE16(exif.length + 2), ...exif],
    [0xff, 0xfe, ...BE16(com.length + 2), ...com],
    [0xff, 0xed, ...BE16(iptc.length + 2), ...iptc],
    dqt, sof, dht, sos, [0xff, 0xd9],
  ]);

  const before = MS.readMetadataSummary(jpeg);
  assert(before.findings.some((f) => f.label === 'Where it was taken' && /37\.808333, 122\.416667/.test(f.value)), 'reads GPS 37.808333, 122.416667');
  assert(before.findings.some((f) => f.value.includes('Canon')), 'reads camera Canon');

  const r = MS.stripBytes(jpeg);
  assert(r.method === 'lossless', 'jpeg stripped losslessly');
  assert(r.removed.some((x) => x.kind === 'exif'), 'removed EXIF');
  assert(r.removed.some((x) => x.kind === 'iptc'), 'removed IPTC');
  assert(r.removed.some((x) => x.kind === 'comment'), 'removed comment');
  assert(r.removed.some((x) => x.kind === 'thumbnail'), 'removed JFIF thumbnail');
  assert(!contains(r.output, 'Exif'), 'output has no EXIF');
  assert(!contains(r.output, 'Photoshop'), 'output has no Photoshop/IPTC');
  assert(!contains(r.output, 'hidden note'), 'output has no comment');
  assert(!contains(r.output, [0xaa, 0xbb, 0xcc]), 'output has no JFIF thumbnail pixels');
  assert(contains(r.output, dqt) && contains(r.output, sof) && contains(r.output, dht), 'quant/frame/huffman tables preserved byte-identical');
  assert(contains(r.output, sos), 'scan data preserved byte-identical');
  // rebuilt APP0 is exactly 18 bytes with zeroed thumbnail dims
  assert(r.output[2] === 0xff && r.output[3] === 0xe0 && r.output[4] === 0x00 && r.output[5] === 0x10, 'APP0 rebuilt to 16-byte length');
  assert(MS.verifyClean(r.output).clean, 'verify: JPEG output clean');
}

// =====================================================================
section('PNG (genuinely valid, via zlib)');
{
  const w = 2, h = 2;
  const rawRows = [];
  const px = [[10, 20, 30, 255], [40, 50, 60, 255], [70, 80, 90, 255], [100, 110, 120, 255]];
  for (let y = 0; y < h; y++) { rawRows.push(0); for (let x = 0; x < w; x++) rawRows.push(...px[y * w + x]); }
  const raw = Buffer.from(rawRows);
  const idatData = zlib.deflateSync(raw);
  const chunk = (type, data) => { const body = [...Buffer.from(type, 'latin1'), ...data]; return [...BE32(data.length), ...body, ...BE32(crc32(U8(body)))]; };
  const ihdr = [...BE32(w), ...BE32(h), 8, 6, 0, 0, 0];
  const text = [...Buffer.from('Comment\0secret data')];
  const exif = [...exifTiff()];
  const time = [...BE16(2024), 6, 15, 12, 0, 0];
  const priv = [...Buffer.from('leak')];
  const png = U8([
    [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
    chunk('IHDR', ihdr), chunk('tEXt', text), chunk('eXIf', exif), chunk('tIME', time),
    chunk('prVt', priv), chunk('IDAT', [...idatData]), chunk('IEND', []),
  ]);

  const before = MS.readMetadataSummary(png);
  assert(before.findings.some((f) => f.label === 'Where it was taken'), 'PNG: reads embedded eXIf GPS');
  assert(before.findings.some((f) => /secret data/.test(f.value)), 'PNG: reads tEXt comment');

  const r = MS.stripBytes(png);
  assert(!contains(r.output, 'secret data'), 'PNG: tEXt removed');
  assert(!contains(r.output, 'leak'), 'PNG: unknown ancillary chunk removed (allow-list)');
  assert(!contains(r.output, 'eXIf') && !contains(r.output, 'Canon'), 'PNG: eXIf removed');
  assert(MS.verifyClean(r.output).clean, 'verify: PNG output clean');

  // output must still be a structurally valid PNG with correct CRCs and identical pixels
  const kept = [];
  let i = 8, idatOut = null, ok = true;
  while (i < r.output.length) {
    const len = (r.output[i] << 24 | r.output[i + 1] << 16 | r.output[i + 2] << 8 | r.output[i + 3]) >>> 0;
    const type = String.fromCharCode(r.output[i + 4], r.output[i + 5], r.output[i + 6], r.output[i + 7]);
    const body = r.output.subarray(i + 4, i + 8 + len);
    const crcGot = (r.output[i + 8 + len] << 24 | r.output[i + 9 + len] << 16 | r.output[i + 10 + len] << 8 | r.output[i + 11 + len]) >>> 0;
    if (crc32(body) !== crcGot) ok = false;
    if (type === 'IDAT') idatOut = r.output.subarray(i + 8, i + 8 + len);
    kept.push(type);
    i += 12 + len;
  }
  assert(ok, 'PNG: every surviving chunk has a valid CRC');
  assert(JSON.stringify(kept) === JSON.stringify(['IHDR', 'IDAT', 'IEND']), 'PNG: only IHDR/IDAT/IEND survive');
  assert(idatOut && Buffer.compare(zlib.inflateSync(Buffer.from(idatOut)), raw) === 0, 'PNG: pixels byte-identical after strip');
}

// =====================================================================
section('WebP (extended RIFF)');
{
  const tiff = [...exifTiff()];
  const xml = [...Buffer.from('<x><dc:creator><rdf:li>Jane Doe</rdf:li></dc:creator><exif:GPSLatitude>37,48N</exif:GPSLatitude><exif:GPSLongitude>122,25E</exif:GPSLongitude></x>')];
  const pad = (a) => (a.length & 1 ? [...a, 0] : a);
  const rchunk = (cc, data) => [...Buffer.from(cc, 'latin1'), ...LE32(data.length), ...pad([...data])];
  const vp8x = rchunk('VP8X', [0x0c, 0, 0, 0, ...[0, 0, 0], ...[0, 0, 0]]); // flags = EXIF|XMP
  const vp8 = rchunk('VP8 ', [1, 2, 3, 4, 5, 6, 7, 8]);
  const exif = rchunk('EXIF', tiff);
  const xmp = rchunk('XMP ', xml);
  const priv = rchunk('prv ', [...Buffer.from('leak')]);
  const body = U8([vp8x, vp8, exif, xmp, priv]);
  const webp = U8([[...Buffer.from('RIFF')], LE32(body.length + 4), [...Buffer.from('WEBP')], [...body]]);

  const before = MS.readMetadataSummary(webp);
  assert(before.findings.some((f) => f.label === 'Where it was taken'), 'WebP: reads EXIF GPS');
  assert(before.findings.some((f) => /XMP/.test(f.label)), 'WebP: detects XMP');

  const r = MS.stripBytes(webp);
  assert(!contains(r.output, 'Canon') && !contains(r.output, [0x45, 0x58, 0x49, 0x46]), 'WebP: EXIF chunk removed');
  assert(!contains(r.output, 'Jane Doe'), 'WebP: XMP chunk removed');
  assert(!contains(r.output, 'leak'), 'WebP: unknown chunk removed (allow-list)');
  assert(contains(r.output, [1, 2, 3, 4, 5, 6, 7, 8]), 'WebP: VP8 image data preserved');
  // VP8X kept, but EXIF/XMP flag bits cleared
  let vp8xFlags = null, i = 12;
  while (i + 8 <= r.output.length) { const cc = String.fromCharCode(r.output[i], r.output[i + 1], r.output[i + 2], r.output[i + 3]); const sz = (r.output[i + 4] | r.output[i + 5] << 8 | r.output[i + 6] << 16 | r.output[i + 7] << 24) >>> 0; if (cc === 'VP8X') vp8xFlags = r.output[i + 8]; i += 8 + sz + (sz & 1); }
  assert(vp8xFlags === 0, 'WebP: VP8X EXIF/XMP flag bits cleared');
  // RIFF size field matches actual remaining bytes
  const riff = (r.output[4] | r.output[5] << 8 | r.output[6] << 16 | r.output[7] << 24) >>> 0;
  assert(riff === r.output.length - 8, 'WebP: RIFF size field recomputed correctly');
  assert(MS.verifyClean(r.output).clean, 'verify: WebP output clean');
}

// =====================================================================
section('dispatch & failure cases');
{
  let threw = '';
  try { MS.stripBytes(U8([[...Buffer.from('GIF89a')], [1, 2, 3, 4, 5, 6]])); } catch (e) { threw = e.code; }
  assert(threw === 'UNSUPPORTED_FORMAT', 'GIF → UNSUPPORTED_FORMAT');
  threw = '';
  try { MS.stripBytes(U8([[0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b]])); } catch (e) { threw = e.code; }
  assert(threw === 'NOT_AN_IMAGE', 'random bytes → NOT_AN_IMAGE');
  // truncated JPEG (APP1 claims more than available) → malformed throw (canvas-fallback path)
  threw = 'none';
  try { MS.stripBytes(U8([[0xff, 0xd8], [0xff, 0xe1, 0xff, 0xf0, 0x45]])); } catch (e) { threw = e.message; }
  assert(threw !== 'none' && /Malformed|past end/.test(threw), 'truncated JPEG throws malformed');
  // detectFormat sanity
  assert(MS.detectFormat(U8([[0xff, 0xd8, 0xff, 0xe0]])) === 'jpeg', 'detect jpeg');
  assert(MS.detectFormat(U8([[0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]])) === 'png', 'detect png');
}

// =====================================================================
section('ZIP (validated by unzip -t)');
{
  const files = [
    { name: 'a.txt', data: new Uint8Array([...Buffer.from('hello world')]) },
    { name: 'photo (1).jpg', data: new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]) },
  ];
  const zip = MS.makeZip(files);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mszip-'));
  const zp = path.join(dir, 'out.zip');
  fs.writeFileSync(zp, Buffer.from(zip));
  let integrity = false, listing = '';
  try { const out = execFileSync('unzip', ['-t', zp], { encoding: 'utf8' }); integrity = /No errors detected/.test(out); listing = out; } catch (e) { listing = String(e); }
  assert(integrity, 'unzip -t reports no CRC errors: ' + listing.split('\n').slice(-3).join(' '));
  try { const a = execFileSync('unzip', ['-p', zp, 'a.txt'], { encoding: 'utf8' }); assert(a === 'hello world', 'unzip extracts a.txt content'); } catch { assert(false, 'unzip -p a.txt failed'); }
  fs.rmSync(dir, { recursive: true, force: true });
}

// =====================================================================
section('review fixes');
{
  // (2) JPEG with data appended after EOI: recorded + dropped, changed=true
  const dqt = [0xff, 0xdb, ...BE16(4), 0, 1], sof = [0xff, 0xc0, ...BE16(5), 8, 0, 1], dht = [0xff, 0xc4, ...BE16(4), 0, 2], sos = [0xff, 0xda, ...BE16(4), 1, 0, 0x11];
  const jpeg = U8([[0xff, 0xd8], dqt, sof, dht, sos, [0xff, 0xd9], [...Buffer.from('APPENDED_MP4_DATA')]]);
  const rj = MS.stripBytes(jpeg);
  assert(rj.changed === true && rj.removed.some((x) => x.kind === 'trailer'), 'JPEG post-EOI trailer recorded (changed=true)');
  assert(!contains(rj.output, 'APPENDED_MP4_DATA') && rj.output.length < jpeg.length, 'JPEG trailer dropped, output smaller');

  // (3) WebP VP8X flag set but no EXIF/XMP chunk: reader sees nothing, but strip reports changed
  const pad = (a) => (a.length & 1 ? [...a, 0] : a);
  const rc = (cc, data) => [...Buffer.from(cc, 'latin1'), ...LE32(data.length), ...pad([...data])];
  const wbody = U8([rc('VP8X', [0x08, 0, 0, 0, 0, 0, 0, 0, 0, 0]), rc('VP8 ', [1, 2, 3, 4])]);
  const wfp = U8([[...Buffer.from('RIFF')], LE32(wbody.length + 4), [...Buffer.from('WEBP')], [...wbody]]);
  assert(MS.readMetadataSummary(wfp).hasAny === false, 'WebP stale-flag: reader finds no metadata');
  const rw = MS.stripBytes(wfp);
  assert(rw.changed === true, 'WebP stale-flag: strip reports changed=true');
  let flags = null, i = 12; while (i + 8 <= rw.output.length) { const cc = String.fromCharCode(rw.output[i], rw.output[i + 1], rw.output[i + 2], rw.output[i + 3]); const sz = (rw.output[i + 4] | rw.output[i + 5] << 8 | rw.output[i + 6] << 16 | rw.output[i + 7] << 24) >>> 0; if (cc === 'VP8X') flags = rw.output[i + 8]; i += 8 + sz + (sz & 1); }
  assert(flags === 0, 'WebP stale-flag: VP8X flag byte cleared');

  // (1) EXIF DoS cap: a GPS IFD with count=0xFFFFFFFF must not hang the reader
  const ent = (tag, type, count, val) => [...LE16(tag), ...LE16(type), ...LE32(count), ...LE32(val)];
  const gpsOff = 8 + 18; // header(8) + ifd0(2+12+4)
  const header = [0x49, 0x49, 0x2a, 0x00, ...LE32(8)];
  const ifd0 = [...LE16(1), ...ent(0x8825, 4, 1, gpsOff), ...LE32(0)];
  const gpsEntries = []; for (let k = 0; k < 64; k++) gpsEntries.push(...ent(2, 1, 0xffffffff, 0));
  const gpsIfd = [...LE16(64), ...gpsEntries, ...LE32(0)];
  const tiff = U8([header, ifd0, gpsIfd]);
  const filler = new Uint8Array(256 * 1024).fill(0x41);
  const dbody = U8([rc('VP8 ', [...filler]), rc('EXIF', [...tiff])]);
  const dwebp = U8([[...Buffer.from('RIFF')], LE32(dbody.length + 4), [...Buffer.from('WEBP')], [...dbody]]);
  const t0 = process.hrtime.bigint();
  MS.readMetadataSummary(dwebp);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  assert(ms < 1000, `EXIF DoS bounded: readMetadataSummary took ${ms.toFixed(0)}ms (<1000)`);

  // (5) 'Other technical tags' no longer double-counts GPS/pointer entries
  const exifOnly = [0x45, 0x78, 0x69, 0x66, 0, 0, ...exifTiff()];
  const gj = U8([[0xff, 0xd8], [0xff, 0xe1, ...BE16(exifOnly.length + 2), ...exifOnly], [0xff, 0xd9]]);
  const gsum = MS.readMetadataSummary(gj);
  assert(gsum.findings.some((f) => f.label === 'Where it was taken'), 'GPS-only: still reports GPS');
  assert(!gsum.findings.some((f) => f.label === 'Other technical tags'), 'GPS-only: no bogus "Other technical tags"');

  // (4) PNG keyword search stays inside its own chunk
  const pchunk = (type, data) => { const body = [...Buffer.from(type, 'latin1'), ...data]; return [...BE32(data.length), ...body, ...BE32(crc32(U8(body)))]; };
  const pp = U8([[0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a], pchunk('tEXt', [...Buffer.from('AAAA')]), pchunk('IEND', [])]);
  const pf = MS.readMetadataSummary(pp).findings.find((x) => /^Text:/.test(x.label));
  assert(pf && pf.label === 'Text: AAAA', `PNG keyword bounded to chunk (got "${pf ? pf.label : 'none'}")`);
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
