# Menu Allergen Matrix Builder

Offline web app that turns a restaurant's own menu into a printable **per-item allergen
disclosure** for the **9 U.S. FDA major allergens** (milk, eggs, fish, crustacean shellfish,
tree nuts, peanuts, wheat, soybeans, **sesame** — added by the FASTER Act, effective Jan 2023).

Enter each dish, tap the allergens (cycle: blank → **● contains** → **○ may contain**), and
print either an **item × allergen grid** or **per-item cards**. Live validation flags unnamed
items and dishes with nothing marked (so "no allergens" is a deliberate, confirmed choice).

**Why now:** state laws are moving from "verbal" to written per-item disclosure (e.g.,
California SB-68 for chains from July 2026; New York for all establishments Nov 2026), and the
enterprise tools (MenuRegistry, EveryBite) are chain-priced — the independent tier is unserved.

## Build
- 100% client-side; **nothing uploaded**; saved in `localStorage`.
- `core.js` — the 9-allergen model, matrix/summary assembly, validation. Pure; browser + Node.
- `index.html` + `app.js` — UI + browser-native **print → PDF**.
- `core.test.js` — `node core.test.js` (19 assertions).

Open `index.html`. No build step, no server.

## Read this
A **disclosure formatting tool**, not allergen testing and not a safety guarantee. Accuracy of
each item's allergens is the establishment's responsibility; the printed grid carries a standard
shared-kitchen cross-contact notice. Confirm your state/local requirements before relying on it.

## Selling it
Public FDA allergen list + the restaurant's own menu = clean on IP/privacy. One-time or
$8–15/mo hosted grid + reprint. Multi-location bills per site.
