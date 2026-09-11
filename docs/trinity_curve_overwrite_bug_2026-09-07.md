# `/trinity` silently overwrites the day's official curve point — found 2026-09-07

**Status:** OPEN. Found by `/zeus` while dispatching `/trinity` on 2026-09-07
(Labor Day). **Not patched** — house rule is to log and open a PR, never to
silently patch shared infrastructure. Zeus is a dispatcher and has no mandate to
edit another owner's code.

**Severity:** latent data loss, currently contained by one fragile invariant.

## What the doc says

`.claude/commands/trinity.md` step 3:

> Call `trinity_dashboard.append_curve_point("cache", god, equity, today)` for each.
> These intraday points are **baked into the dashboard HTML — they don't need to be
> separately persisted** (each god's main run writes the official daily curve point).

That describes points that live in the dashboard. It is wrong about the mechanism.

## What the code does

`trinity_dashboard.append_curve_point` writes **directly to the god's real curve
file** on disk:

```python
path = os.path.join(cache_dir, f"{god}_curve.json")
pts = _load_curve(path)
pts = [p for p in pts if p.get("date") != date]      # <-- deletes the day's real row
pts.append({"date": date, "equity": float(equity)})  # <-- replaces it with a 2-field stub
json.dump(pts, open(tmp, "w"), indent=2)             # <-- always a BARE LIST
```

Two distinct defects:

**1. The day's rich row is destroyed.** A god's curve point carries far more than
`{date, equity}`. Oracle's 2026-09-07 point, written minutes earlier by `/oracle`,
had 11 fields including `session`, `cash`, `positions`, `spy`, `peak_equity`,
`drawdown`, `mark_basis`, and a multi-paragraph `note` documenting the D4 sector
tagging. `append_curve_point` deletes that row by date and appends a two-field
stub in its place. Prior days survive; **only the current day is flattened** —
which is precisely the day a god just finished documenting.

**2. Proteus's envelope is destroyed.** `_load_curve` correctly special-cases
Proteus, whose file is `{"marks": [...]}` rather than a bare list, and returns the
inner list. But `append_curve_point` then `json.dump`s that list back as the whole
file. The `{"marks": ...}` envelope is gone. Any subsequent
`json.load(...)["marks"]` — which is what `/proteus` itself does when marking the
curve — raises `TypeError`/`KeyError`. Proteus's curve is, by his own charter,
*the* scoreboard.

## Why nothing has broken yet

One invariant, and only one: **`/trinity` persists only the dashboard HTML**, under
the `shared` prefix (trinity.md step 5). The mangled curve files stay local and are
overwritten by the next `pantheon.hydrate()`.

That invariant holds *only because `zeus.md` orders `/trinity` last.* If any god
runs after `/trinity` in the same session and persists its own curve, it persists
the stub — and the real row, note and all, is gone from `claude/live` permanently.
The ordering rule in zeus.md is currently load-bearing for data integrity, and
nothing in the code says so.

## What this session did

Ran `/trinity` as specified (the dashboard genuinely needed it — it was last built
Friday 10:33 ET, so the rebuild advanced it to Friday's closes), then restored all
16 `cache/*_curve.json` files from a pre-run snapshot and verified md5s
byte-identical. `cache/oracle_curve.json` and `cache/proteus_curve.json` are
confirmed intact (oracle: 115 points, last row 11 keys with `note` present;
proteus: `{"marks": [...]}`, 58 marks).

## Suggested fixes (for whoever owns this)

1. **Merge, don't replace.** If a row for `date` already exists, update its
   `equity` and leave every other field alone.
2. **Round-trip the envelope.** `_load_curve` already knows whether the file was a
   bare list, `{"points": ...}` or `{"marks": ...}`; `append_curve_point` must
   write back the same shape.
3. **Or make the doc true** — have trinity keep its intraday points in a separate
   `cache/trinity_intraday.json` and never touch a god's curve file at all. This is
   the cleanest option and matches what trinity.md already claims happens.
4. Whichever is chosen, add a regression test covering the Proteus `marks` shape
   and the "existing rich row survives" case.

Until then: **`/trinity` must stay last in the zeus dispatch order**, and that
should be stated in `trinity_dashboard.py` as a comment, not left implicit in
`zeus.md`.
