# Photorealism test harnesses

Playwright scripts that drive `draw/index.html` in a headless Chromium.
They are how every change in this app gets verified; none of them touch
real Firebase.

## Running

Serve the app first, from the repo root:

    nohup python3 -m http.server 8899 --directory draw >/dev/null 2>&1 &

Then run any script with `node`. Chromium lives at `/opt/pw-browsers/chromium`.

| Script | What it proves |
|---|---|
| `_syn.js` | every inline `<script>` block parses (run after EVERY edit) |
| `regress.js quick` | 5 viewports x 2 button sizes, layout overflow and clipping |
| `firstrun.js <tag>` | the fresh-install intro and tour walk through cleanly |
| `acct_test.js` | the account panel renders and opens in each shell |
| `fbreal_test.js` | the REAL Firebase SDK initialises against the live project |
| `shell_test.js` | sign-in routes correctly in browser / new shell / old shell |
| `sync_test.js` | upload, wipe, pull back, no duplicates, delete does not resurrect |
| `meta_test.js` | project progress and comparison captures cross devices |
| `live_test.js` | a capture auto-pushes and a remote change auto-pulls, with timings |
| `pill_test.js` | the "Sign in to sync" pill sits between the rule and the thumbnails |

## The two fake backends

`fbfake/` is a hand-written stand-in for the Firebase modular SDK: an
in-memory store with a working `onSnapshot`, served to the page by
intercepting `https://www.gstatic.com/firebasejs/**`. It is what makes
two-device sync testable without credentials.

`fbreal_test.js` instead serves the genuine SDK from disk (download it
into `fbsdk/` with curl from gstatic) because this sandbox cannot reach
the CDN. Use it to confirm every symbol the app calls actually exists in
the pinned SDK version.

## Gotchas learned the hard way

- `GRID_READY` is a top-level `let`. Use the bare identifier inside
  `page.evaluate`, never `window.GRID_READY`.
- Installing a `window.RealismCam` stub before the page opens a project
  breaks the open path. Only stub it around the moment you need it.
- `page.goto` waits for `load`, which can be later than the splash
  finishing. To measure boot timings, sample from `addInitScript`.
- GoatCounter beacons fail in the sandbox. Those console errors are
  expected and unrelated.
