# UnTraceable

A tiny, single-purpose browser tool that removes **all** identifying and
location metadata from **JPEG, PNG and WebP** photos — GPS, EXIF, XMP, IPTC,
embedded thumbnails, timestamps, camera serials — **entirely in the browser**,
with **zero permissions** and **no network access**. It shows you exactly what
each photo was leaking, strips it losslessly (the pixels are untouched), then
**re-scans its own output** and proves the file is clean.

No backend. No accounts. No dependencies. No build step. Reads top to bottom in
one sitting.

## Why it exists

Photos carry hidden data. Post one to Marketplace and it can broadcast your home
GPS coordinates, your phone's serial number, and a thumbnail that still shows
the *original, un-cropped* image. Cheap "EXIF removers" leak — they delete the
visible EXIF block but leave XMP GPS, the IPTC caption, or that embedded
thumbnail behind. UnTraceable can't leak, because of how it works (below).

## How it works — the one idea

**Allow-list, never a deny-list.** An image file is a container of segments;
some draw the picture, the rest are metadata. UnTraceable keeps **only** the
segments needed to draw the picture faithfully (image data + colour profile) and
drops **everything else** — known, unknown, compressed, or duplicated. A
deny-list ("remove the blocks I know about") can never be proven complete
because containers allow arbitrary and custom segments. An allow-list is
complete *by construction*: a leak-carrier that isn't on the keep-list is simply
never copied. After stripping, it re-parses the output and confirms nothing
identifying survived — the "Verified clean" badge.

The compressed pixel bytes are never touched, so cleaning is **lossless** — the
photo looks identical, just without the hidden data. (Colour profiles are kept:
they carry no identity, and dropping them would visibly change your photo.)

## Install (load unpacked)

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top-right).
3. **Load unpacked** → select this folder.
4. Click the UnTraceable toolbar icon → the tool opens in a tab → drag photos in.

Works in Chrome/Chromium/Edge/Brave/Opera. It also runs as a plain web page:
open `tool.html` directly, or the single-file build (below).

## Files

| File | What it is |
|------|-----------|
| `manifest.json` | MV3 manifest — zero permissions, zero host permissions |
| `background.js` | Service worker — opens `tool.html` on toolbar click (5 lines) |
| `tool.html` / `tool.css` | The UI |
| `src/strip.js` | **The core.** Pure byte-surgery stripper (JPEG/PNG/WebP allow-lists) |
| `src/exif.js` | Pure metadata reader (TIFF/EXIF/GPS parser) + `verifyClean()` |
| `src/zip.js` | Minimal STORE-method ZIP writer (for "Download all") |
| `src/app.js` | DOM layer — drag-drop, rendering, canvas fallback, downloads |
| `icons/` | Generated PNG icons |
| `tools/make-icons.mjs` | Regenerate the icons (pure Node, no deps) |
| `tools/build-standalone.mjs` | Inline everything → `dist/untraceable.html` |
| `tests/core.test.mjs` | Node test suite for the pure core |
| `SPEC.md` | One-page spec (goals + the long non-goals list) |
| `STORE_LISTING.md` | Chrome Web Store copy + review-form answers + monetization |
| `PRIVACY.md` | Privacy statement (it collects nothing) |

The `src/*.js` files are IIFE **classic scripts** (not ES modules) that attach to
a global `MS` namespace. That's deliberate: the *same* files run inside the
extension **and** when `tool.html` is opened from `file://` (ES modules are
blocked by CORS on `file://`). No bundler, no transpiler, no `node_modules`.

## Develop

```sh
node tests/core.test.mjs        # run the core test suite (40 assertions)
node tools/make-icons.mjs       # regenerate icons/
node tools/build-standalone.mjs # produce dist/untraceable.html (single file)
```

The tests eval the three pure core files into Node and drive them with synthetic
files whose metadata is known: they check that a real (zlib-built) PNG comes out
byte-identical in its pixels with all metadata gone, that JPEG tables and scan
data survive untouched, that WebP flag bits are reconciled, and that the ZIP
passes a real `unzip -t` CRC check.

## Scope

**Handles:** JPEG (.jpg/.jpeg), PNG (.png), WebP (.webp).
**Deliberately does not:** HEIC/TIFF/GIF/BMP/AVIF/RAW, any image editing,
metadata *viewing/writing*, page/context-menu integration, or anything that
needs a network. See `SPEC.md` for the full non-goals list — it's longer than
the goals list on purpose.

## Selling it (one-time price, walk away)

The Chrome Web Store can't charge for extensions (payments removed in 2020–2021,
still gone in 2026). The zero-maintenance path: list this **free** on the store
as discovery, and sell `dist/untraceable.html` as a one-time download on a
Merchant-of-Record store (Payhip / Lemon Squeezy) that handles checkout and tax.
The buyer double-clicks one file that runs offline forever. See `STORE_LISTING.md`.

## License

MIT (see `LICENSE`). Do whatever you like with it.
