# Subcue — subtitle fixer & converter

A **local-first** web app that opens a subtitle file, tells you exactly what's wrong with it,
and fixes/converts it — **100% in your browser.** Nothing is uploaded, which is the whole point:
the people who most need this (editors, translators, course/podcast producers, agencies) are
working on **unreleased** video and can't paste it into a random web tool.

Reads and writes **SRT · WebVTT · SBV**, tolerant of the real-world mess: UTF-8 BOM, CRLF, dot-
vs-comma milliseconds, hour-less timestamps, missing indices, and VTT `NOTE`/`STYLE` blocks.

## What it does
- **"What's wrong with it"** — a report of overlaps, out-of-order cues, zero/negative durations,
  too-fast reading speed (CPS), over-long lines, too many lines, empty cues.
- **Convert** between SRT / WebVTT / SBV.
- **Shift** the whole track earlier or later.
- **Sort** and remove empty cues.
- **Sync to a re-cut** *(Pro)* — give two known points ("this line is at 00:00:58, it should be
  at 00:01:00" and one later pair) and Subcue solves the linear map, fixing **drift and offset
  at once**. This is the killer feature — matching subs to a different edit of the video.
- **Framerate conversion** *(Pro)* — the classic PAL 23.976 ↔ 25 drift, and more.
- **One-click auto-fix** *(Pro)* — sort, enforce a minimum on-screen duration, resolve overlaps
  with a clean gap.
- **Strip formatting tags** *(Pro)* — `<i>`, `<font>`, ASS overrides like `{\an8}`.

Everything runs on a single format-agnostic cue model (`{start, end, text}` in milliseconds), so
transforms never care what the source format was. Verify in 10 seconds: load a broken file, see
the red issue list, click auto-fix, watch it clear.

## Build
- 100% client-side; **nothing uploaded**; no build step, no server. Open `index.html`.
- `core.js` — the engine: parse/serialize + all transforms + the `analyze()` linter. Pure;
  browser + Node.
- `license.js` — offline Pro-key verification (ECDSA P-256 via Web Crypto). Public key only.
- `index.html` + `app.js` — drag-drop load, encoding pick, issue report, ops, preview, download.
- `core.test.js` — `node core.test.js` (57 assertions).
- `license.test.js` — `node license.test.js` (sign/verify roundtrip, 8 assertions).

## Free vs Pro
Free = open/convert/shift/sort + the full issue report (the hook). **Pro** ($14 one-time) adds
sync-to-a-recut, framerate conversion, one-click auto-fix, and tag stripping — the operations
that solve the *hard* problems. Pro unlocks via a signed license key verified **in the browser**
— no login, no license server, works offline forever on that machine.

### License keys (offline, no backend)
`tools/make-license-keys.js` mints signed keys and bakes the matching **public** key into
`license.js`:

```
node tools/make-license-keys.js 100      # → tools/license-keys.csv (upload to Payhip)
```

- The **private** signing key lives in `tools/signing-key.json` — **gitignored; never commit
  it**; back it up. Re-run the tool with the same key file to mint more; old keys keep working.
- Upload `tools/license-keys.csv` to your checkout's license-key list; each sale hands the buyer
  one key. Buyers paste it into **Unlock Pro**; the app verifies the signature locally.

## Selling it
Deterministic, testable, zero-maintenance (a few stable formats, no API, no data feed), and the
free incumbents are ad-choked upload-based sites. The privacy angle is a real moat. Full store/
landing copy, pricing, FAQ, screenshot shot-list, seed communities, and Payhip setup are in
`LISTING.md`; promo renders are in `promo/`.
