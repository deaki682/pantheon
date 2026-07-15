# Menu Allergen Matrix Builder — store & landing copy

A ready-to-paste kit for a Payhip / Gumroad / Lemon Squeezy product page, plus the free
web-app hook. Everything below is written to be accurate against the July 2026 US allergen
law landscape (sources at the bottom). **Don't overstate the law** — the tool's value is
that it makes the disclosure *easy and clean*, not that it is legally required everywhere.

---

## Product name
**Menu Allergen Matrix Builder** (short: "Allergen Matrix")

Tagline options:
- **"Turn your menu into a clean allergen chart in ten minutes — printed, not uploaded."**
- "The 9-allergen menu grid, built in your browser. No account, no data leaves your laptop."
- "Give allergy guests a straight answer — and hand your staff one page that says it."

---

## Short description (Payhip subtitle / meta, ~160 chars)
Build a printable per-item allergen chart for the 9 FDA major allergens. Runs entirely in
your browser — nothing uploaded. Free grid; Pro adds cards, branding & saved menus.

---

## Long description (product page body)

Every server has fielded it mid-rush: *"does the pad thai have peanuts?"* — and the honest
answer is a shrug. **Menu Allergen Matrix Builder** turns your menu into a clean, printable
grid that answers it in one glance, for all nine FDA major allergens: milk, eggs, fish,
crustacean shellfish, tree nuts, peanuts, wheat, soybeans, and **sesame** (the 9th, added by
the FASTER Act and declared like the others since January 2023).

You tap each item's allergens — **● contains** or **○ may contain (shared kitchen)** — and it
builds a wall- or menu-ready chart. Print the grid for the kitchen line, or per-item cards for
the counter. It's the kind of per-item disclosure the disclosure landscape is now moving
toward: in 2026 **California's ADDE Act (SB 68)** became the first US law to require restaurants
to show the major allergens for each menu item — for chains of 20+ California locations — and
similar per-item menu bills have been introduced in several other states. Whether or not a law
covers you yet, a straight allergen answer is table stakes for allergy guests.

**Why operators like it**
- **10-second result.** Tap, print. No spreadsheet, no designer, no PDF wrestling.
- **100% in your browser.** Your menu never leaves your laptop — nothing uploaded, no account,
  no login. (That's also why there's no monthly fee.)
- **All 9 FDA allergens, incl. sesame** — with a "may contain / shared kitchen" state and a
  built-in cross-contact note.
- **Print to PDF or paper** with your browser's print dialog. Re-print any time your recipe
  changes — it's your file.
- **One-time price. No subscription.** Buy it once, use it forever, offline.

**Free vs Pro**

| | Free | **Pro** |
|---|:---:|:---:|
| Printable 9-allergen grid | ✓ | ✓ |
| All 9 FDA allergens + "may contain" | ✓ | ✓ |
| Cross-contact disclosure note | ✓ | ✓ |
| Runs 100% locally, no account | ✓ | ✓ |
| **Per-item allergen cards** (counter/takeout) | | ✓ |
| **Your logo + custom footer** on every printout | | ✓ |
| **Unlimited saved menus** (lunch / dinner / 2nd location) | | ✓ |

**Pro is a one-time $12.** You get a license key by email; paste it into the app and Pro
unlocks — verified right in your browser, so it keeps working offline forever, on that
machine, with no login.

> **Please read:** This is a *disclosure and formatting tool*, not allergen testing, a
> lab analysis, or a safety guarantee — and not legal advice. You enter the allergen
> information; you're responsible for its accuracy and for meeting any rules that apply to
> your business. Because kitchens share equipment, no tool can rule out cross-contact.

---

## Price
- **Free** web app (the grid) — the hook and the SEO/word-of-mouth engine.
- **Pro: $12 one-time** (test $9 vs $15; $12 is the anchor). No subscription, no VAT surprises —
  the checkout (Payhip/Lemon Squeezy) is merchant of record and handles EU/UK VAT.

## FAQ

**Is my menu uploaded anywhere?** No. It's a static page; everything you type stays in your
browser's local storage. Close the tab and it's still there next time on that machine.

**Does this make me compliant with [my state]?** It produces the per-item allergen chart such
laws call for, but *compliance is your call* — rules vary by state and by whether they apply to
your business (California's SB 68, for example, applies to chains of 20+ CA locations). Use it
as the tool; confirm your obligations with your local health authority.

**Do I need an account or internet?** No account, ever. You need internet once to load the page
(and to buy Pro); after that it runs offline.

**How does the Pro key work without a login?** Your key is digitally signed. The app checks the
signature locally with your browser's built-in crypto — no server, no phone-home. That's why it
works offline and we never see your data.

**Can I use it on two computers?** The key unlocks Pro per browser. Paste it on each machine you
use. (Please don't share keys publicly — it's a one-person tool at a one-person price.)

**Refunds?** Yes — it's a $12 tool; if it doesn't help, ask and you'll get your money back.

---

## Screenshot shot-list (for the store gallery)
1. **The builder, populated** (`index.html?demo`) — the tap-to-cycle allergen chips. *Hero.*
2. **The printed grid** — print-preview of the matrix (File → Print → Save as PDF).
3. **Per-item cards** (Pro) — the counter/takeout card layout.
4. **The Pro comparison table** (free vs pro) — rendered as an image.
5. **"100% local" trust panel** — the no-upload/no-account promise.

## Suggested seed communities (where allergy-tool demand actually lives)
- r/restaurateur, r/KitchenConfidential, r/smallbusiness (show-don't-sell: "made a free
  allergen-chart builder, no signup")
- Local restaurant-association newsletters / FB groups, especially California (SB 68 timing)
- Food-truck and bakery groups (packaged-label states like NY are tightening too)
- Celiac / food-allergy advocacy forums — they *want* more restaurants to publish charts

---

## Payhip setup (offline license keys)
1. Create the product (digital download or "no file / external" — the app is free-hosted; Pro is
   just the key). Price $12.
2. Run `node tools/make-license-keys.js 100` → produces `tools/license-keys.csv` (100 keys) and
   bakes the matching public key into `license.js`.
3. In Payhip: product → **License keys → Import** → upload `license-keys.csv`. Payhip hands one
   key per sale and emails it to the buyer automatically.
4. Host `allergen-matrix/` as a static site (Payhip's own page can link to it; or Netlify/GitHub
   Pages/Cloudflare Pages — it's just static files).
5. Point the app's "Get a key" button at your Payhip product URL (edit `#buyLink`'s `href` in
   `index.html`).
6. **Back up `tools/signing-key.json`** somewhere safe and never commit it. Re-run the tool with
   the same key file to mint more keys as you sell out — existing keys keep working.

---

## Verified legal facts (sources — checked July 2026)
- **9 FDA major allergens + sesame via FASTER Act, effective Jan 1 2023** (packaged-food
  *labels*; does not itself mandate menus): FDA, "The FASTER Act: Sesame Is the Ninth Major
  Food Allergen."
- **California ADDE Act / SB 68** — signed Oct 13 2025, **in force July 1 2026**, applies to
  **chains of 20+ CA locations**, per-item allergen disclosure on menu or via QR + written
  alternative: CA Legislature SB 68; CA Restaurant Association; ArentFox Schiff.
- **New York (Chapter 494, ~Nov 2026)** — allergen **labels on deli/bakery-style packaged
  foods prepared on-premises**, *not* made-to-order menu disclosure. Do **not** market it as a
  menu law.
- **Massachusetts / Illinois** — allergen **awareness/training** laws (menu notice + staff
  training), not per-item disclosure.
- **Maryland, Illinois (HB 4686), Michigan, Missouri, others** — per-item menu bills
  **introduced, not enacted**. Describe as "proposed," never as current requirements.
- **Federal** — **no** general per-item restaurant allergen mandate. FALCPA covers packaged
  labels; the federal menu-labeling rule covers *calories* for 20+ chains, not allergens.

**Claims to avoid:** "federal law requires menu allergen disclosure" (false); "California
requires all restaurants" (only 20+ chains); "New York requires it on menus" (it's packaged
labels); listing pending bills as current law; calling any per-item menu mandate "nationwide."
