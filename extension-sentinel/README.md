# Extension Sentinel — permission watchdog (MV3)

Shows what **every installed extension can actually access**, ranked by risk — and, the point,
**alerts you when a trusted extension quietly gains scary permissions after an update** (the
exact pattern behind the 2025–26 "sold-to-adware" wave, where a Featured extension changes
owners and pushes a weaponized update to everyone).

- Reads only what `chrome.management` already exposes about your own installed extensions.
- Scores each by its permissions (broad host access, `webRequest`, `cookies`, `debugger`,
  `proxy`, `nativeMessaging`, `management`, …) with a plain-English reason per flag.
- Stores a local snapshot and, on each open, **diffs** it: new installs, removals, and
  **permission creep** since your last check.
- **100% local.** No host permissions, no network, no telemetry — which is the whole point of
  a *trust* tool. Permissions requested: `management` (to read the list) + `storage` (the snapshot).

## Build
- `core.js` — risk scoring + snapshot diff. Pure; runs in the popup and under Node.
- `core.test.js` — `node core.test.js` (22 assertions, incl. the permission-creep detector).
- `popup.html` / `popup.js` — the report UI.
- `make-icons.js` — regenerates the shield icons (zero deps).

Load unpacked: `chrome://extensions` → Developer mode → **Load unpacked** → this folder.

## The idea
From the "did my extension turn evil?" concept — the most *original* idea the market recon
surfaced. The moat compounds if you later add a shared database of known ownership changes;
the local single-user version here is the clean, shippable core. Trust-first positioning
(local, open, zero-telemetry) is exactly what the telemetry-funded incumbents can't copy.
