# Photorealism — handover

State as of web **v397** / Android **versionCode 224** (`0.9.190`).
Branch: `claude/latest-drawing-app-version-0h2lp6`. Owner: Dylan
(deaki682@gmail.com).

## What this is

A single-file web app (`draw/index.html`, ~9k lines, no build step) that
helps traditional artists draw photorealistically: import a reference,
grid it, break it into value layers, then photograph your drawing and
compare. It ships three ways:

- **Web / PWA** at realismdrawing.com (`draw/` uploaded as a flat zip)
- **Android** (`android/`, package `app.realism.draw`), live on Play. The
  native shell runs a local HTTP server and points a WebView at it, so
  the web app IS the app.
- **iOS** (`ios/`), TestFlight; App Store 1.0 was submitted on build 68.

~550 daily actives, mostly Android. Ad supported (AdMob native) with a
one-time `remove_ads` purchase.

## Accounts and sync (built 2026-09, the current work)

Optional Google sign-in, then references sync between devices.

- Firebase project **photorealism-838e5**, project number 1096368575946.
- Config is inline in `index.html` (`FB_CFG`). These values are public by
  design; `firebase/*.rules` is what protects the data.
- SDK loads lazily from gstatic, pinned to `FB_VER`. Nothing loads until
  the Account panel is opened or a previous session was signed in.

**What travels:** the reference image (byte for byte, no re-encode), its
name and thumbnail, the per-project state (`fmt det circ time gtot done
mode lay edit def`), and the comparison photo of the drawing with its
crop and adjustments.

**What does not:** the four shipped starter references, and the cooked
caches, which are recomputable.

**Triggers, all automatic.** Push: `galAdd` (any new reference),
`cmpSaveNow` (any capture), `openPhoto` (progress), leaving the drawing
screen. Pull: a Firestore `onSnapshot` listener, detached while
backgrounded, plus `visibilitychange`. The Sync now button is an
override that should never be needed.

**Why sign-in is native on Android.** Google refuses OAuth inside a
WebView (`disallowed_useragent`), so the shell signs in with Credential
Manager, falls back to the older `GoogleSignIn` picker when that returns
"no credentials", and hands the page only an ID token, which
`window.__authToken` turns into a Firebase credential.

### The three SHA-1 fingerprints, and why

Google matches package + signing certificate. All three are registered
on the Android app in Firebase, and all three are needed:

| Fingerprint | Covers |
|---|---|
| `B6:2C:89:32:CA:8F:49:D6:E7:38:88:33:06:FC:BE:44:B3:37:CA:CF` | Play app signing — real users |
| `F8:92:FD:73:C1:EF:52:CF:07:DC:14:83:09:43:E5:99:F2:32:5C:BF` | Play **internal app sharing** — Dylan's own testing |
| `2A:33:64:6F:08:99:5C:21:0D:E1:DF:C1:45:42:5A:07:7A:CE:14:9A` | the upload key — locally installed builds |

The middle one cost hours. Internal app sharing re-signs with a
per-developer key that appears in **no console page**. The only way to
see it was making the app print its own certificate, which it now does
in the `DEVELOPER_ERROR 10` message. Reach for that first next time.

### Bucket CORS

`firebase/cors.json` is applied to `gs://photorealism-838e5.firebasestorage.app`.
Without it every download is blocked, because the Android shell serves
itself from `127.0.0.1` on a port that changes each launch, so no fixed
origin list can match. Re-apply with:

    gcloud storage buckets update gs://photorealism-838e5.firebasestorage.app --cors-file=firebase/cors.json

## Environment

Each remote session gets a fresh container. What survives is only what is
committed, so:

**Present from the image** (verified): `/opt/android-sdk`,
`/opt/gradle-8.14.3/bin/gradle`, `/opt/pw-browsers/chromium`, python3,
zip, node 22.

**NOT present — install it first.** The harnesses need `playwright-core`,
which lived in a session scratchpad and dies with it:

    cd <your scratchpad>            # or anywhere outside the repo
    npm install playwright-core

Then run the scripts from that directory, or set `NODE_PATH` to its
`node_modules`. Do not add it to the repo; it is a 100MB+ dependency for
a project that otherwise has no build step at all.

Chromium is already downloaded, so never run `playwright install`.
`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` is set for you.

**The signing key is committed** (`android/release.keystore` and
`android/keystore.properties`), so a fresh session can build a signed
release immediately. That is convenient and it is also the single most
dangerous thing in this repo: losing or rotating that key means no
future update can ever be published to the existing Play listing. It is
worth backing both files up somewhere outside GitHub.

**The sandbox cannot reach some hosts.** gstatic is unreachable from the
headless browser, which is why `fbfake/` exists; GoatCounter beacons
fail too. `curl` works through the agent proxy, so downloading the real
SDK to serve locally is fine.

## Shipping a change

1. Edit `draw/index.html` (and `android/` if native).
2. `node tools/photorealism-tests/_syn.js` — after every edit, no exceptions.
3. Run the relevant harnesses (see that folder's README).
4. Bump all three together: `<span id="verNum">vNNN</span>`, the `sw.js`
   cache name, and `versionCode` / `versionName` in `app/build.gradle`.
5. Build: `cd android && export ANDROID_HOME=/opt/android-sdk && /opt/gradle-8.14.3/bin/gradle bundleRelease --no-daemon -q`
6. Zip the 19 files from `draw/` (see any recent commit for the list).
7. Send Dylan both files. Commit with absolute paths, push to the branch.

**Never** put a model identifier in a commit message, PR or any pushed
artifact.

**Never** dispatch an iOS/TestFlight build unless Dylan explicitly asks.

## Outstanding

**Dylan's side**
- Update Play Data Safety: the app now collects email addresses and
  photos, both linked to the user, both deletable. The current
  declaration contradicts this and mismatches get apps suspended.
- Raise the Google Cloud budget alert from $20 to ~$60 AUD; full-quality
  uploads cost roughly 8x what downscaled ones would.
- App Store 1.0 review result unknown. If approved, flip the
  realismdrawing.com/ios redirect to the live listing.
- AdMob bidding: waiting on Meta and AppLovin account IDs. Add them as
  **bidding** sources, not waterfall, so no manual eCPM is needed.

**Code**
- **iOS is well behind.** No native sign-in at all, and a stack of Swift
  across several sessions has never been compiled (the AdController
  rewrite among it). The first TestFlight build will probably fail to
  compile.
- **Apple sign-in is broken, not merely unbuilt.** The provider is
  enabled but has no code flow, so it fails on web and cannot work on
  Android. Needs Services ID, Team ID, Key ID and `.p8`. The button is
  hidden on Android; still visible on web.
- Sync has no conflict resolution beyond last-writer-wins on timestamps,
  which is fine for one person with two devices and not for more.
- The audit workflow `wf_7dec7f78-2e1` was interrupted mid-verify. The
  leftovers are cleanup-grade.

## Ideas discussed, not built

Purchase portability across devices (kills "I paid and still see ads"),
progress timelines built from the already-tracked time-per-drawing and
dated captures, and settings sync. Deliberately rejected: shared
galleries or challenges, because user-generated content drags in
moderation and reporting obligations onto one person.
