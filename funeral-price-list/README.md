# Funeral Rule Price List Generator

A single-page, offline web app that assembles the four documents the **FTC Funeral Rule
(16 CFR Part 453)** requires a funeral provider to give consumers — from the home's own
items and prices:

- **General Price List (GPL)** — with the Rule's required mandatory disclosures
- **Casket Price List**
- **Outer Burial Container Price List**
- (an itemized **Statement** is generated at arrangement time from the same data)

**Why it exists:** the Rule has been mandatory since 1994, ~19,000 US homes must comply,
the disclosure formatting is exacting, and the FTC ships only sample templates — no
generator. Small owner-run homes hack it in Word and risk a formatting-based enforcement slip.

## How it's built
- 100% client-side. **Nothing is uploaded**; data is saved in `localStorage`.
- `core.js` — the whole product: the FTC **model** mandatory-disclosure sentences, the 16
  GPL categories, document assembly, and a validator that flags missing required items.
  Pure and dependency-free; runs in the browser and under Node.
- `index.html` + `app.js` — the form and browser-native **print → PDF** output (no libraries).
- `core.test.js` — `node core.test.js` (23 assertions: disclosures, assembly, validation, totals).

Open `index.html` in any browser. No build step, no server.

## Important, read this
This tool generates a **draft** using the FTC's **model** disclosure language and your own
prices. It is **not legal advice** and does not guarantee compliance. The Rule was amended
recently and **states add their own requirements** — review every output against the current
16 CFR Part 453 text and your state licensing board before giving it to a consumer. The
mandatory-disclosure wording should be confirmed against the current Rule.

## Selling it (notes)
Public federal rule + the home's own data = clean on IP and privacy (no PHI, no licensed
code sets). Frame as "produces a Funeral-Rule-formatted draft you review," never "guaranteed
compliant." One-time license or low annual sub; reprint-on-price-change is the recurring hook.
