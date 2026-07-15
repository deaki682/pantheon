// zip.js — a minimal, dependency-free ZIP writer (STORE method, no compression).
// Loaded as a plain <script>; attaches MS.makeZip to the global namespace.
//
// Images are already compressed, so storing them uncompressed costs almost
// nothing and keeps this file tiny and unbreakable. ZIP's format has been frozen
// for decades. We emit: [local header + data]×N, then the central directory,
// then the end-of-central-directory record. All fields are little-endian.
(function () {
  'use strict';
  const MS = (globalThis.MS = globalThis.MS || {});

  const CRC_TABLE = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(bytes) {
    let c = 0xffffffff;
    for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }

  const u16 = (a, v) => { a.push(v & 0xff, (v >>> 8) & 0xff); };
  const u32 = (a, v) => { a.push(v & 0xff, (v >>> 8) & 0xff, (v >>> 16) & 0xff, (v >>> 24) & 0xff); };

  const DOS_DATE = 0x0021; // 1980-01-01, fixed so archives are deterministic
  const DOS_TIME = 0x0000;
  const FLAG_UTF8 = 0x0800; // filenames are UTF-8

  // files: [{ name: string, data: Uint8Array }] → Uint8Array (a .zip)
  MS.makeZip = function (files) {
    const enc = new TextEncoder();
    const parts = [];
    const central = [];
    let offset = 0;

    for (const f of files) {
      const nameBytes = enc.encode(f.name);
      const crc = crc32(f.data);
      const size = f.data.length;

      const lh = [];
      u32(lh, 0x04034b50);
      u16(lh, 20); u16(lh, FLAG_UTF8); u16(lh, 0);          // version, flags, store
      u16(lh, DOS_TIME); u16(lh, DOS_DATE);
      u32(lh, crc); u32(lh, size); u32(lh, size);
      u16(lh, nameBytes.length); u16(lh, 0);
      const lhBytes = new Uint8Array(lh);
      parts.push(lhBytes, nameBytes, f.data);

      u32(central, 0x02014b50);
      u16(central, 20); u16(central, 20); u16(central, FLAG_UTF8); u16(central, 0);
      u16(central, DOS_TIME); u16(central, DOS_DATE);
      u32(central, crc); u32(central, size); u32(central, size);
      u16(central, nameBytes.length); u16(central, 0); u16(central, 0);
      u16(central, 0); u16(central, 0); u32(central, 0);
      u32(central, offset);
      for (const bb of nameBytes) central.push(bb);

      offset += lhBytes.length + nameBytes.length + f.data.length;
    }

    const centralBytes = new Uint8Array(central);
    parts.push(centralBytes);

    const eocd = [];
    u32(eocd, 0x06054b50);
    u16(eocd, 0); u16(eocd, 0);
    u16(eocd, files.length); u16(eocd, files.length);
    u32(eocd, centralBytes.length); u32(eocd, offset);
    u16(eocd, 0);
    parts.push(new Uint8Array(eocd));

    let total = 0; for (const p of parts) total += p.length;
    const out = new Uint8Array(total);
    let o = 0; for (const p of parts) { out.set(p, o); o += p.length; }
    return out;
  };
})();
