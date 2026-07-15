// make-icons.mjs — regenerate the extension icons with zero image dependencies.
// Pure Node (zlib only). Draws a location pin crossed by a slash ("no location")
// on a rounded brand-blue square, supersampled 4× for anti-aliasing.
//
//   node tools/make-icons.mjs
//
// Kept in the repo so the icons are reproducible years from now.
import zlib from 'node:zlib';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'icons');
const SS = 4; // supersample factor

// ---- PNG encoder (RGBA, 8-bit) ----
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(buf) { let c = 0xffffffff; for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }
function chunk(type, data) {
  const t = Buffer.from(type, 'latin1');
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0);
  const body = Buffer.concat([t, data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function encodePNG(w, h, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 6; // 8-bit, RGBA
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; rgba.copy ? rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, y * w * 4 + w * 4) : raw.set(rgba.subarray(y * w * 4, y * w * 4 + w * 4), y * (w * 4 + 1) + 1); }
  const idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);
}

// ---- geometry helpers (signed distances; <0 means inside) ----
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function sdRoundRect(px, py, cx, cy, hw, hh, r) {
  const qx = Math.abs(px - cx) - (hw - r), qy = Math.abs(py - cy) - (hh - r);
  const ox = Math.max(qx, 0), oy = Math.max(qy, 0);
  return Math.hypot(ox, oy) + Math.min(Math.max(qx, qy), 0) - r;
}
const sdCircle = (px, py, cx, cy, r) => Math.hypot(px - cx, py - cy) - r;
function sdSegment(px, py, ax, ay, bx, by, r) {
  const dx = bx - ax, dy = by - ay;
  const t = clamp(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0, 1);
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy)) - r;
}
// pin = a circle head + a triangle tip meeting at the bottom
function insidePin(px, py, cx, headY, headR, tipY) {
  if (sdCircle(px, py, cx, headY, headR) < 0) return true;
  // triangle from tip (cx,tipY) up to the head's tangent width
  const tw = headR * 0.86; // half-width where the triangle meets the head
  if (py >= headY && py <= tipY) {
    const frac = (tipY - py) / (tipY - headY);
    const halfW = tw * frac;
    if (Math.abs(px - cx) <= halfW) return true;
  }
  return false;
}

const BRAND = [37, 99, 168], WHITE = [255, 255, 255], RED = [219, 68, 55];

function renderSize(size) {
  const W = size * SS, H = size * SS;
  const acc = new Float64Array(W * H * 4);
  const cx = W / 2;
  const headY = H * 0.40, headR = W * 0.20, tipY = H * 0.74, holeR = W * 0.083;
  // slash endpoints (top-right to bottom-left), inset from the rounded square
  const m = W * 0.20;
  const ax = W - m, ay = m, bx = m, by = H - m;
  const slashHalo = W * 0.085, slashCore = W * 0.055;

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const px = x + 0.5, py = y + 0.5;
      let r = 0, g = 0, b = 0, a = 0;
      if (sdRoundRect(px, py, cx, H / 2, W / 2 - W * 0.03, H / 2 - H * 0.03, W * 0.22) < 0) {
        [r, g, b] = BRAND; a = 255;
        if (insidePin(px, py, cx, headY, headR, tipY) && sdCircle(px, py, cx, headY, holeR) >= 0) { [r, g, b] = WHITE; }
        if (sdSegment(px, py, ax, ay, bx, by, slashHalo) < 0) { [r, g, b] = WHITE; }
        if (sdSegment(px, py, ax, ay, bx, by, slashCore) < 0) { [r, g, b] = RED; }
      }
      const o = (y * W + x) * 4;
      acc[o] = r; acc[o + 1] = g; acc[o + 2] = b; acc[o + 3] = a;
    }
  }
  // box-downsample SS×SS → 1
  const out = Buffer.alloc(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let dy = 0; dy < SS; dy++) for (let dx = 0; dx < SS; dx++) {
        const o = ((y * SS + dy) * W + (x * SS + dx)) * 4;
        r += acc[o]; g += acc[o + 1]; b += acc[o + 2]; a += acc[o + 3];
      }
      const n = SS * SS, o = (y * size + x) * 4;
      out[o] = Math.round(r / n); out[o + 1] = Math.round(g / n); out[o + 2] = Math.round(b / n); out[o + 3] = Math.round(a / n);
    }
  }
  return encodePNG(size, size, out);
}

fs.mkdirSync(OUT, { recursive: true });
for (const s of [16, 32, 48, 128]) {
  fs.writeFileSync(path.join(OUT, `icon${s}.png`), renderSize(s));
  console.log(`icon${s}.png`);
}
