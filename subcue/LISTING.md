# Subcue — store & landing copy

Paste-ready kit for a Payhip / Gumroad / Lemon Squeezy page + the free web-app hook.

---

## Product name
**Subcue** — subtitle fixer & converter

Taglines:
- **"Fix, re-time, and convert subtitles — without uploading a single frame."**
- "The subtitle file was made for a different cut. Subcue re-syncs it in two clicks."
- "Every free SRT tool wants you to upload your unreleased video's subtitles. This one doesn't."

---

## Short description (~160 chars)
Open, fix and convert SRT/VTT/SBV subtitles 100% in your browser — nothing uploaded. Re-sync to
a new cut, fix overlaps & framerate drift, convert formats. Free core; Pro $14.

---

## Long description

Subtitles are always *almost* right. They're off by two seconds. They were timed for the 25 fps
broadcast master and your file is 23.976. Two cues overlap. Half of them flash by too fast to
read. They came as VTT and your player wants SRT. **Subcue fixes all of it — and it never uploads
your file**, because the people who do this work are usually holding an unreleased edit that has
no business being pasted into a random ad-farm website.

Drop in an **SRT, WebVTT, or SBV** file. Subcue reads it — even when it's a mess of BOM markers,
Windows line endings, comma-vs-dot milliseconds, and missing indices — and immediately tells you
**what's wrong**: overlaps, out-of-order cues, impossible durations, lines that read too fast,
lines that are too long. Then you fix it and export in whatever format you need.

**The one that saves an afternoon:** *Sync to a re-cut.* You know one line should land at
00:01:00 and a late line should land at 00:59:57 — type those two pairs and Subcue solves the
timing math, correcting **drift and offset in a single pass**. No more nudging 1,400 cues by hand.

**Why people keep it in their toolbar**
- **Nothing is uploaded. No account.** It's a static page; your file is read locally. That's the
  whole pitch for anyone under NDA or working pre-release.
- **Reads the real-world mess** — BOM, CRLF, dot/comma ms, hour-less timestamps, VTT NOTE/STYLE.
- **Tells you what's broken** before you ship it — overlaps, CPS reading-speed, long lines.
- **One-time price. No subscription.** Buy once, use forever, offline.

**Free vs Pro**

| | Free | **Pro** |
|---|:---:|:---:|
| Open SRT · WebVTT · SBV (tolerant parser) | ✓ | ✓ |
| Convert between all three formats | ✓ | ✓ |
| Shift the whole track earlier / later | ✓ | ✓ |
| "What's wrong" report (overlaps, fast cues, long lines) | ✓ | ✓ |
| Sort & remove empty cues | ✓ | ✓ |
| **Sync to a different cut** (2-point drift + offset) | | ✓ |
| **Framerate conversion** (23.976 ↔ 25 PAL, etc.) | | ✓ |
| **One-click auto-fix** (overlaps, min duration, gaps) | | ✓ |
| **Strip formatting tags** (`<i>`, `{\an8}`, …) | | ✓ |

**Pro is a one-time $14.** You get a license key by email; paste it into the app and Pro unlocks
— verified right in your browser, so it works offline forever, on that machine, no login.

> Subcue edits subtitle *timing and formatting*. It doesn't translate, transcribe, or check that
> your text is correct — that part's on you.

---

## Price
- **Free** web app (open / convert / shift / report) — the hook and the word-of-mouth engine.
- **Pro: $14 one-time** (test $9 vs $19). No subscription; the checkout (Payhip/Lemon Squeezy) is
  merchant of record and handles EU/UK VAT.

## FAQ

**Is my file uploaded?** No. Subcue is a static page; your subtitle is read in your browser and
never sent anywhere. That's deliberate — it's built for people working on unreleased material.

**What formats?** Reads and writes **SRT, WebVTT (.vtt), and SBV**. It's tolerant of malformed
files (BOM, CRLF, dot/comma milliseconds, missing cue numbers).

**My accents show as gibberish (é → Ã©).** Your file isn't UTF-8. Switch the encoding dropdown to
Windows-1252 and it re-reads correctly.

**What's "sync to a re-cut"?** When subtitles were timed for a different edit of the video, they
drift — right at the start, more wrong by the end. Give Subcue two known points (a line's current
time and where it *should* be) and it re-times the whole file to match. Pro feature.

**Does the Pro key need internet or a login?** No. Your key is digitally signed; the app checks
the signature locally with your browser's built-in crypto. Works offline; we never see anything.

**Two computers?** The key unlocks Pro per browser — paste it on each machine. Please don't post
keys publicly; it's a one-person tool at a one-person price.

**Refunds?** Yes — it's $14; if it doesn't help, ask.

---

## Screenshot shot-list (store gallery)
1. **The app with a messy file loaded** (`index.html?demo`) — the issue report lit up. *Hero.*
2. **Before → after** — the "5 issues" state next to the "2 issues, overlaps fixed" state
   (`index.html?demo` vs `index.html?demo&fixed`).
3. **The sync-to-a-recut panel** — the two-point inputs (this is the money feature).
4. **The free-vs-Pro table** (`promo/promo-compare.png`).
5. **"Nothing uploaded" trust line** — the local-first promise.

## Suggested seed communities
- r/editors, r/VideoEditing, r/davinciresolve, r/premiere, r/Filmmakers (post the free tool:
  "made a local-first subtitle fixer, doesn't upload your file")
- Translator / subtitler forums (ProZ, r/TranslationStudies, subtitling Discords)
- r/podcasting, r/NewTubers, online-course creator groups (they wrestle YouTube SBV/VTT)
- Accessibility/captioning communities — they care about CPS and line-length limits

## Payhip setup (offline license keys)
1. Create the product, price $14 (digital / "external" — the app is free-hosted; Pro is the key).
2. `node tools/make-license-keys.js 100` → `tools/license-keys.csv` + bakes the public key into
   `license.js`.
3. Payhip → product → **License keys → Import** → upload `license-keys.csv`. One key per sale,
   emailed automatically.
4. Host `subcue/` as a static site (Netlify / GitHub Pages / Cloudflare Pages — just static files).
5. Point the "Get a key" button at your product URL (edit `#buyLink`'s `href` in `index.html`).
6. **Back up `tools/signing-key.json`**, never commit it. Re-run the tool with the same key file
   to mint more keys as you sell out — existing keys keep working.

## Honesty notes (don't overstate)
- It edits timing/formatting, not content — it doesn't translate or transcribe. Say so.
- "Nothing uploaded" is literally true (static page, local read) — it's the strongest claim; keep
  it accurate by never adding analytics or a network call.
- Encoding auto-detection isn't magic; the manual encoding switch is the honest fallback.
