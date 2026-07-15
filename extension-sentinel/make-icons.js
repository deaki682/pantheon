/* Zero-dependency PNG icons: a teal shield with a white check. node make-icons.js */
'use strict';
var fs = require('fs'), path = require('path'), zlib = require('zlib');
var CRC = (function () { var t = []; for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c >>> 0; } return t; })();
function crc32(b) { var c = 0xFFFFFFFF; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function chunk(type, data) { var len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0); var body = Buffer.concat([Buffer.from(type, 'ascii'), data]); var crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body), 0); return Buffer.concat([len, body, crc]); }
function png(w, h, rgba) {
  var sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  var ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  var raw = Buffer.alloc((w * 4 + 1) * h);
  for (var y = 0; y < h; y++) { raw[y * (w * 4 + 1)] = 0; rgba.copy(raw, y * (w * 4 + 1) + 1, y * w * 4, (y + 1) * w * 4); }
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}
function distSeg(px, py, x1, y1, x2, y2) { var dx = x2 - x1, dy = y2 - y1, l2 = dx * dx + dy * dy, t = l2 ? ((px - x1) * dx + (py - y1) * dy) / l2 : 0; t = Math.max(0, Math.min(1, t)); return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)); }

function shieldInside(nx, ny) { // nx in [-1,1], ny in [0,1]
  if (ny < 0 || ny > 1) return false;
  var hw;
  if (ny <= 0.5) hw = 0.86; else hw = 0.86 * (1 - (ny - 0.5) / 0.5);
  if (ny < 0.16) { var k = (0.16 - ny) / 0.16; hw *= Math.sqrt(Math.max(0, 1 - k * k)); } // round top
  return Math.abs(nx) <= hw;
}

function render(size) {
  var SS = 4, W = size * SS, H = size * SS, out = Buffer.alloc(size * size * 4);
  var teal = [13, 148, 136], white = [255, 255, 255];
  var cx = W / 2, top = H * 0.08, bot = H * 0.94, halfW = W * 0.40, th = W * 0.10;
  // check segments in normalized shield space -> pixel space
  function nToPx(nx, ny) { return [cx + nx * halfW, top + ny * (bot - top)]; }
  var a = nToPx(-0.34, 0.52), b = nToPx(-0.05, 0.70), c = nToPx(0.42, 0.30);
  function sample(fx, fy) {
    var nx = (fx - cx) / halfW, ny = (fy - top) / (bot - top);
    if (!shieldInside(nx, ny)) return [0, 0, 0, 0];
    var d = Math.min(distSeg(fx, fy, a[0], a[1], b[0], b[1]), distSeg(fx, fy, b[0], b[1], c[0], c[1]));
    return d <= th / 2 ? white.concat(255) : teal.concat(255);
  }
  for (var Y = 0; Y < size; Y++) for (var X = 0; X < size; X++) {
    var r = 0, g = 0, bl = 0, al = 0;
    for (var sy = 0; sy < SS; sy++) for (var sx = 0; sx < SS; sx++) {
      var p = sample(X * SS + sx + 0.5, Y * SS + sy + 0.5);
      r += p[0]; g += p[1]; bl += p[2]; al += p[3];
    }
    var n = SS * SS, o = (Y * size + X) * 4;
    out[o] = Math.round(r / n); out[o + 1] = Math.round(g / n); out[o + 2] = Math.round(bl / n); out[o + 3] = Math.round(al / n);
  }
  return png(size, size, out);
}
var dir = path.join(__dirname, 'icons'); fs.mkdirSync(dir, { recursive: true });
[16, 48, 128].forEach(function (s) { fs.writeFileSync(path.join(dir, 'icon' + s + '.png'), render(s)); console.log('icons/icon' + s + '.png'); });
