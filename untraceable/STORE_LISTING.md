# UnTraceable — Chrome Web Store listing

Everything you paste into the Developer Dashboard, plus the review-form answers
that stop a small extension getting rejected. Written to the 2025–2026 program
policies (developer.chrome.com/docs/webstore/program-policies).

---

## Name (45 char max)

```
UnTraceable — Erase Photo Location & EXIF
```

## Short description / summary (132 char max)

```
Erase the hidden GPS location, device ID & metadata from your JPEG, PNG & WebP photos. 100% on your device — nothing is uploaded.
```

## Category

`Productivity` (secondary fit: `Tools`).

## Full description

```
Every photo you take carries hidden data. Before you post a picture to
Marketplace, a forum, a dating profile, or send it to a stranger, it can quietly
reveal the GPS coordinates where you took it (often your home), the exact date
and time, your camera or phone's serial number, the editing software you used,
and even a hidden thumbnail that can still show the ORIGINAL, un-cropped image.

UnTraceable removes all of it — in your browser, on your computer, and nowhere
else.

WHAT IT DOES
• Drag in one photo or a whole batch of JPEG, PNG and WebP images.
• It shows you exactly what each photo was leaking — GPS location, camera make
  and serial number, timestamps, author, software, embedded thumbnails — so you
  can see the risk before you clear it.
• It strips EVERYTHING identifying: EXIF (including GPS and hidden thumbnails),
  XMP, IPTC/Photoshop captions, comments and timestamps.
• Then it re-scans the cleaned file and shows a "Verified clean" badge, so you
  don't just trust it — you can see it worked.
• Download each cleaned photo, or all of them at once as a ZIP.

TRULY PRIVATE — BY DESIGN
• 100% offline. Your photos are never uploaded, because there is no server to
  upload them to. Turn off your Wi-Fi and UnTraceable still works — the proof.
• No account, no sign-up, no cloud, no tracking, no analytics.
• Requests ZERO permissions. It cannot read your browsing, your other tabs, or
  anything on the web. It only ever sees the files you drag in.

IT KEEPS YOUR PHOTO INTACT
Most tools either miss things or quietly re-compress your image and shift its
colours. UnTraceable does neither. It keeps only the parts of the file that draw
the picture — the image data and the colour profile — and drops the rest. The
pixels are untouched: the cleaned photo looks identical, just without the
hidden data.

WHO IT'S FOR
• Anyone selling on Marketplace/Craigslist who doesn't want buyers to see where
  they live.
• Journalists, researchers and anyone protecting a source or their own safety.
• Real-estate, HR, insurance and support staff who must remove location data
  before sharing photos.
• Anyone who just doesn't want their camera serial number and home coordinates
  travelling with every picture they share.

SUPPORTED FORMATS
JPEG (.jpg/.jpeg), PNG (.png) and WebP (.webp). Damaged files are safely
re-rendered as a fallback (you're told when that happens).

UnTraceable does one thing and does it correctly. No feeds, no upsells, no
subscription.
```

## Single purpose (required dashboard field)

```
UnTraceable removes identifying and location metadata (EXIF, GPS, XMP, IPTC,
thumbnails, timestamps) from JPEG, PNG and WebP image files that the user drags
into the extension's page. All processing happens locally in the browser.
```

## Permissions & justifications

**UnTraceable requests no permissions and no host permissions.** This is the
strongest possible position for review — there is nothing to justify, and it
removes the entire class of "unused/over-broad/unjustified permission"
rejections. If a reviewer asks, the honest statements are:

- **permissions:** none declared. All work uses standard web APIs available to
  an extension page with no permission (File drag-drop, ArrayBuffer/Blob, an
  anchor `download`). The toolbar click opens the extension's own bundled page
  via `chrome.tabs.create` on its own extension URL, which requires no
  permission (the `tabs` permission is only needed to read other tabs' URLs or
  titles — UnTraceable never does).
- **host permissions:** none. UnTraceable never touches any website, so it needs
  no host access and declares no content scripts and no match patterns.

## Data use — dashboard Privacy tab (required for every item, even zero-data)

- **Remote code:** "No, I am not using remote code." All logic is in the
  package; nothing is fetched or `eval`'d.
- **Data collection disclosure:** UnTraceable collects **none** of the listed
  categories. Leave every box unchecked and declare that no user data is
  collected, used, or transmitted. (The photos are read into memory to process
  them and are never stored or sent anywhere.)
- **Limited Use certification:** affirm both boxes — UnTraceable does not sell or
  transfer user data, and does not use it for anything beyond the single
  purpose above (there is no data flow at all).
- **Privacy policy URL:** not required, because UnTraceable stores and transmits
  no user data (it doesn't even persist a setting). A one-paragraph policy is
  included anyway (`PRIVACY.md`) — host it and paste the link if you prefer to
  over-disclose; it only helps trust.

## Screenshots to capture (1280×800 or 640×400; at least 1, ideally 5)

1. **The hook — a photo's secrets exposed.** Drop a phone photo; capture the
   card showing "GPS location 37.77…, -122.41…", "Camera Apple iPhone…",
   "Camera serial number", "Embedded thumbnail". Caption: *"See what your photo
   is leaking."*
2. **Verified clean.** The same card after stripping, green "✓ Verified clean"
   badge, size before→after. Caption: *"One click. Provably clean."*
3. **Batch.** A dozen files processed at once with the "Download all (ZIP)" bar.
   Caption: *"Clean a whole album in seconds."*
4. **The offline proof.** The empty drop zone with the line "turn off your
   Wi-Fi — it still works", ideally with the browser's offline indicator
   visible. Caption: *"Nothing is uploaded. There's no server to upload to."*
5. **Zero permissions.** The Chrome "This extension can read and change… —
   nothing" install prompt / details panel showing no permissions requested.
   Caption: *"Requests no permissions. It only sees the files you drag in."*

Store icon: `icons/icon128.png`. Promo tile art can reuse the pin-with-slash
mark on the brand-blue field.

## Reality check on charging (read before you plan pricing)

The Chrome Web Store removed paid extensions and its payments/licensing API in
2020–2021 and **still has no way to charge for an extension in 2026.** You
cannot sell this extension through the store. The zero-maintenance, walk-away
way to earn the one-time $5–15 is:

- **List this extension free on the Chrome Web Store (and Firefox AMO)** as a
  discovery funnel, and
- **Sell the identical tool as a one-file download** (`dist/untraceable.html`,
  produced by `tools/build-standalone.mjs`) on a Merchant-of-Record store —
  **Payhip** (5%, no monthly fee) or **Lemon Squeezy** (5% + $0.50). They host
  checkout and remit global sales tax, so there is nothing to keep alive. The
  buyer double-clicks the file; it runs offline forever, no key, no login.

Because the tool is loaded as classic scripts (not ES modules), the single
built HTML file runs directly from `file://` with no server — which is exactly
what makes the download a genuine walk-away product.
