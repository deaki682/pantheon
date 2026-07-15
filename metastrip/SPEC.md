# MetaStrip — one-page spec

**One job:** drag in photos, get back the *same* photos with every piece of
identifying and location metadata removed, and *see* exactly what was removed.
100% in the browser, offline, no upload, no accounts, no permissions.

The value is **correctness**: cheap strippers leave things behind (the EXIF
thumbnail that still holds the un-edited original, XMP GPS that survives an
EXIF-only wipe, IPTC captions). MetaStrip keeps *only the bytes needed to draw
the picture* and drops the rest — then re-scans its own output and shows a
"Verified clean" badge. If it can't verify, it says so.

---

## Goals (the whole product)

1. Accept one or many **JPEG / PNG / WebP** images by drag-drop or file picker.
2. Remove **all** identity/location metadata, losslessly (pixels untouched):
   EXIF (incl. GPS **and** the embedded thumbnail), XMP + Extended XMP,
   IPTC / Photoshop IRB, JFIF/JFXX thumbnail, comments, timestamps, MakerNotes.
   Keep **only** render-critical + colour data (image scan / IDAT, quant &
   Huffman tables, ICC colour profile) so the picture looks identical.
3. Before stripping, **show what was found** per image — GPS coordinates, camera
   make/model/serial, lens serial, date taken, software, author, copyright,
   "embedded thumbnail of the original", and a count of remaining technical tags.
4. After stripping, **re-scan the output** and show **Verified clean** (or flag
   anything that survived).
5. **Download** each cleaned image, or **all as a ZIP**.
6. Everything is **local**: works with the network physically off; no server, no
   accounts, **zero permissions**, no telemetry.

## Non-goals (deliberately out — this list is the product's spine)

- **No other formats.** No HEIC/HEIF, TIFF, GIF, BMP, AVIF, or camera RAW
  (CR2/NEF/ARW/DNG…). JPEG/PNG/WebP only. Unsupported files get a clear message,
  never a silent pass.
- **No editing of any kind.** No crop, resize, rotate, compress, colour, filter,
  watermark, or format conversion. It removes metadata; it does not touch the
  picture.
- **No re-compression by default.** Pixels are copied byte-for-byte. A malformed
  file that can't be parsed losslessly falls back to a canvas re-encode **only
  with an explicit "re-encoded — may recompress" warning**, never silently.
- **No metadata *viewer*/exporter.** It shows what it *removes*; it is not a
  full EXIF browser, map plotter, or metadata report tool.
- **No metadata *writing*.** No "set copyright/author", no tagging, no adding a
  watermark or a "cleaned by" mark.
- **No partial/selective keep.** No "keep camera model, drop GPS" toggles. It
  strips the lot. (The colour profile is the one thing kept — it carries no
  identity and dropping it visibly changes the photo.)
- **No web-page integration.** No right-click-an-image context menu, no reading
  images off pages, no fetching remote URLs, no content scripts, no host
  permissions. This is *why* it needs zero permissions and can't break when a
  site changes.
- **No network anything.** No cloud, sync, accounts, login, history, saved
  settings, update feed, analytics, error reporting, or A/B.
- **No backend, no license server, no database.** Nothing to keep alive.
- **No folders / recursion / directory watching.** Individual files only in v1.
- **No PDF redaction** (safe redaction of PDFs is genuinely hard; deliberately
  excluded to keep the correctness promise honest).
- **No i18n** (English only), **no theming/settings**, **no mobile** (desktop
  Chromium). **No build step**, **no framework**, **no dependencies.**

## Smallest version that's still worth $5

Drag-drop → strip JPEG/PNG/WebP losslessly → "here are the GPS coordinates and
camera serial we found and removed" → **Verified clean** badge → download (one
or ZIP), entirely offline with zero permissions. Nothing above this line is
optional; nothing below the Non-goals line ships.

## Why it won't break in two years

- Depends only on **frozen file-format specs** (JPEG/JFIF, EXIF/TIFF, PNG, WebP
  RIFF, XMP, IPTC) and **stable browser primitives** (File, Blob, ArrayBuffer,
  anchor download). No DOM of any website, no API, no key, no server.
- Zero permissions → nothing for a Chrome policy change to invalidate.
- No dependencies → no supply chain to rot, no `npm audit` treadmill.
- One tab, a few hundred lines of commented vanilla JS you can re-read in a
  sitting.
