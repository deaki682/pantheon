# Menu Allergen Matrix Builder

Offline web app that turns a restaurant's own menu into a printable **per-item allergen
disclosure** for the **9 U.S. FDA major allergens** (milk, eggs, fish, crustacean shellfish,
tree nuts, peanuts, wheat, soybeans, **sesame** — added by the FASTER Act, declared like the
others since Jan 2023).

Enter each dish, tap the allergens (cycle: blank → **● contains** → **○ may contain**), and
print either an **item × allergen grid** or **per-item cards**. Live validation flags unnamed
items and dishes with nothing marked (so "no allergens" is a deliberate, confirmed choice).

**Why now:** the disclosure landscape is moving from verbal to written per-item disclosure —
**California's ADDE Act (SB 68)** requires it of restaurant chains with 20+ CA locations from
**July 1 2026**, and per-item menu bills have been introduced in several other states. Whether
or not a law covers a given operator yet, a clean allergen answer is table stakes for allergy
guests, and the enterprise tools are chain-priced — the independent tier is unserved.
*(Accurate scope of each law is in `LISTING.md`; do not overstate it — e.g. New York's 2026
law is packaged deli/bakery **labels**, not menu disclosure, and there is no federal per-item
mandate.)*

## Build
- 100% client-side; **nothing uploaded**; saved in `localStorage`.
- `core.js` — the 9-allergen model, matrix/summary assembly, validation. Pure; browser + Node.
- `license.js` — offline Pro-key verification (ECDSA P-256 via Web Crypto). Public key only.
- `index.html` + `app.js` — UI, browser-native **print → PDF**, Pro gating, unlock modal.
- `core.test.js` — `node core.test.js` (19 assertions).
- `license.test.js` — `node license.test.js` (sign/verify roundtrip, 9 assertions).

Open `index.html`. No build step, no server.

## Free vs Pro
Free = the printable allergen **grid** (the hook). **Pro** ($12 one-time) adds **per-item
cards**, **your logo + custom footer** on printouts, and **unlimited saved menus**. Pro unlocks
via a signed license key verified **in the browser** — no login, no license server, works
offline forever on that machine.

### License keys (offline, no backend)
`tools/make-license-keys.js` mints a batch of signed keys and bakes the matching **public** key
into `license.js`:

```
node tools/make-license-keys.js 100      # → tools/license-keys.csv (upload to Payhip)
```

- The **private** signing key lives in `tools/signing-key.json` — **gitignored; never commit
  it**; back it up. Re-run the tool with the same key file to mint more keys; existing keys
  keep working.
- Upload `tools/license-keys.csv` to your checkout's license-key list (Payhip → product →
  License keys → Import). Each sale hands the buyer one key.
- Buyers paste the key into **Unlock Pro**; the app verifies the signature locally. If you
  ever regenerate the keypair, previously sold keys stop verifying — so keep the key file.

## Read this
A **disclosure formatting tool**, not allergen testing and not a safety guarantee, and not
legal advice. Accuracy of each item's allergens is the establishment's responsibility; the
printed grid carries a standard shared-kitchen cross-contact notice. Confirm your state/local
requirements before relying on it.

## Selling it
Public FDA allergen list + the restaurant's own menu = clean on IP and privacy (nothing
uploaded). Free grid as the hook; **one-time $12 Pro** unlock. Full store/landing copy, FAQ,
pricing, screenshot shot-list, seed communities, and the verified legal fact sheet are in
`LISTING.md`. Promo renders are in `promo/`.
