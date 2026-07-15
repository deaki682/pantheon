/*
 * Generates the toolbar/store icons with zero dependencies (Node's zlib only):
 * a rounded blue tile with a white guillemet «. Run: node tools/make-icons.js
 */
'use strict';
var fs = require('fs');
var path = require('path');
var zlib = require('zlib');

// ---- PNG encoding ----
var CRC_TABLE = (function () {
  var t = [];
  for (var n = 0; n < 256; n++) {
    var c = n;
    for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  var c = 0xFFFFFFFF;
  for (var i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function chunk(type, data) {
  var len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0);
  var typeBuf = Buffer.from(type, 'ascii');
  var body = Buffer.concat([typeBuf, data]);
  var crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function encodePNG(width, height, rgba) {
  var sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  var ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0; // 8-bit RGBA
  var raw = Buffer.alloc((width * 4 + 1) * height);
  for (var y = 0; y < height; y++) {
    raw[y * (width * 4 + 1)] = 0; // filter: none
    rgba.copy(raw, y * (width * 4 + 1) + 1, y * width * 4, (y + 1) * width * 4);
  }
  var idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);
}

// ---- drawing ----
function distToSeg(px, py, x1, y1, x2, y2) {
  var dx = x2 - x1, dy = y2 - y1;
  var l2 = dx * dx + dy * dy;
  var t = l2 ? ((px - x1) * dx + (py - y1) * dy) / l2 : 0;
  t = Math.max(0, Math.min(1, t));
  var cx = x1 + t * dx, cy = y1 + t * dy;
  return Math.hypot(px - cx, py - cy);
}

function render(size) {
  var SS = 4, W = size * SS, H = size * SS;
  var bg = [0x25, 0x63, 0xEB], fg = [255, 255, 255];
  var radius = W * 0.22;
  var cy = H / 2;
  var armW = W * 0.15, armH = H * 0.28, th = W * 0.085;
  var tips = [W * 0.36, W * 0.58]; // two left-pointing chevrons -> «

  function insideRounded(x, y) {
    var qx = Math.min(Math.max(x, radius), W - radius);
    var qy = Math.min(Math.max(y, radius), H - radius);
    var dx = x - qx, dy = y - qy;
    return dx * dx + dy * dy <= radius * radius;
  }
  function onGlyph(x, y) {
    for (var i = 0; i < tips.length; i++) {
      var tx = tips[i];
      var d = Math.min(
        distToSeg(x, y, tx, cy, tx + armW, cy - armH),
        distToSeg(x, y, tx, cy, tx + armW, cy + armH)
      );
      if (d <= th / 2) return true;
    }
    return false;
  }

  var out = Buffer.alloc(size * size * 4);
  for (var Y = 0; Y < size; Y++) {
    for (var X = 0; X < size; X++) {
      var r = 0, g = 0, b = 0, a = 0;
      for (var sy = 0; sy < SS; sy++) {
        for (var sx = 0; sx < SS; sx++) {
          var fx = X * SS + sx + 0.5, fy = Y * SS + sy + 0.5;
          if (!insideRounded(fx, fy)) continue;
          var col = onGlyph(fx, fy) ? fg : bg;
          r += col[0]; g += col[1]; b += col[2]; a += 255;
        }
      }
      var n = SS * SS, o = (Y * size + X) * 4;
      out[o] = Math.round(r / n); out[o + 1] = Math.round(g / n);
      out[o + 2] = Math.round(b / n); out[o + 3] = Math.round(a / n);
    }
  }
  return encodePNG(size, size, out);
}

var dir = path.join(__dirname, '..', 'icons');
fs.mkdirSync(dir, { recursive: true });
[16, 32, 48, 128].forEach(function (s) {
  fs.writeFileSync(path.join(dir, 'icon' + s + '.png'), render(s));
  console.log('wrote icons/icon' + s + '.png');
});
