"""Neglect-leg sourcing — the below-floor fundamentals screen (2026-07-06).

The third and highest-yield Oracle sourcing leg. The forced-seller sweep finds
EVENTS (a tender, a wind-down, a spinoff — something is filed); the neglect leg
finds STATES — names quietly trading below a real, countable balance-sheet floor
with no event to trip a form index. Empirically this is the family that produced
4 of the 5 names Oracle liked pre-rebuild (ARVN/VTSI/ALCO/RNA): a small,
uncovered stock priced below its net cash / net-net / tangible book, where the
mispricing is STRUCTURAL NEGLECT — no analyst, no index, no forced buyer — not an
event. The forced-seller net cannot see these; only a whole-universe fundamentals
sweep can.

The screen is the COVERAGE stage — deliberately generous — and every name it
emits still faces the full precision gate (`make_convex_dossier` →
`verify_dossier` → `rank_fundable`). It does NOT assert a floor is real; it
asserts a floor is CLAIMED by the last filed balance sheet and the price sits
below it. The verification gate is what decides whether that floor survives
goodwill, a full debt-stack reconciliation, and a primary-source read — the exact
traps that killed MNRO (goodwill book) and XRN (phantom net-cash) at launch.

Two disciplines baked in, both bought dearly by the launch-gate kills:

  1. NET CASH IS NET OF THE FULL DEBT LINE. cashneq + current investments − TOTAL
     debt. XRN's dossier called it "debt-free" off one balance-sheet line and
     missed a $652.7M credit facility. The screen nets against `debt`
     (Sharadar's total-debt field) so a levered "cash-rich" name never surfaces
     as net-cash.

  2. A BURNING FLOOR IS A MELTING FLOOR. A net-cash name bleeding operating cash
     has a floor with a fuse (ARVN's caveat). The screen computes a cash-runway
     and FLAGS (does not drop) short-runway names so the dossier stage prices the
     erosion instead of trusting a static number.

Everything here is a pure function of already-pulled data (Sharadar SF1 balance
sheets + DAILY marketcap + TICKERS metadata) — no network, fully testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# --- coverage dials (generous; the precision gate is what filters) ----------
NEGLECT_CAP_USD = 3_000e6      # $3B — neglect lives small; large-caps are covered
MIN_CAP_USD = 10e6            # $10M — below this the quote is untradable noise
MIN_RUNWAY_Q = 8             # <8 quarters of burn covered by the floor = eroding, FLAG
# Financials (banks/insurers) net-cash & tangible-book are meaningless — their
# balance sheet IS leveraged float. Excluded at the sector gate.
EXCLUDE_SECTORS = frozenset({"Financial Services"})
# Mortgage REITs sit under the Real Estate SECTOR but are financials in disguise:
# their "book" is a leveraged, marked-to-model MORTGAGE-LOAN portfolio (mBS +
# repo), not a hard property floor. A mREIT at 0.6x book is the industry NORM,
# not a convex floor. Excluded at the industry gate (equity REITs — REIT-Office/
# Residential/Industrial, which own real buildings — are KEPT; their book is a
# genuine, if illiquid, transacting-asset floor the precision gate can test).
EXCLUDE_INDUSTRIES = frozenset({"REIT - Mortgage"})
# Common stock only (incl. ADRs / Canadian) — no warrants, preferred, units,
# funds, ETNs. A category must START with one of these AND not be a warrant.
_COMMON_PREFIXES = ("Domestic Common Stock", "ADR Common Stock", "Canadian Common Stock")

# floor ladder, hardest -> softest, mapped to the verification gate's FLOOR_BASIS
# vocabulary. net_cash and ncav are both `net_net` basis (0.9); tangible book is
# `book` (0.55, the softer one the MNRO goodwill trap guards).
_FLOOR_ORDER = ("net_cash", "ncav", "tangible_book")
_FLOOR_BASIS = {"net_cash": "net_net", "ncav": "net_net", "tangible_book": "book"}


def _num(row: dict, key: str) -> float:
    v = row.get(key)
    return float(v) if v is not None else 0.0


@dataclass(frozen=True)
class Floors:
    """The three countable floors from one balance sheet, all in dollars."""
    net_cash: float        # cashneq + current investments − TOTAL debt
    ncav: float            # total current assets − TOTAL liabilities (Graham net-net)
    tangible_book: float   # common equity − intangibles (incl. goodwill)


def floors(row: dict) -> Floors:
    """Compute the three floors from a Sharadar SF1 balance-sheet row (dollars).

    net_cash nets against `debt` (Sharadar's TOTAL debt), not one line — the XRN
    discipline. ncav is Graham's net-current-asset value (current assets less ALL
    liabilities, senior and not). tangible_book strips intangibles+goodwill (the
    MNRO discipline; Sharadar folds goodwill into `intangibles`)."""
    cash = _num(row, "cashneq") + _num(row, "investmentsc")
    net_cash = cash - _num(row, "debt")
    ncav = _num(row, "assetsc") - _num(row, "liabilities")
    tangible_book = _num(row, "equity") - _num(row, "intangibles")
    return Floors(net_cash=net_cash, ncav=ncav, tangible_book=tangible_book)


def best_floor(mcap_usd: float, fl: Floors) -> Optional[dict]:
    """The HARDEST floor the price sits below, or None if the price is above them
    all. Returns {floor_type, floor_basis, floor_usd, discount} where discount =
    1 − mcap/floor (positive ⇒ trading below that floor).

    Hardest-first so a name below net cash is reported as net_cash (not merely
    'below book') — the strongest true statement about it."""
    vals = {"net_cash": fl.net_cash, "ncav": fl.ncav, "tangible_book": fl.tangible_book}
    for ftype in _FLOOR_ORDER:
        floor = vals[ftype]
        if floor > 0 and mcap_usd < floor:
            return {
                "floor_type": ftype,
                "floor_basis": _FLOOR_BASIS[ftype],
                "floor_usd": floor,
                "discount": round(1.0 - mcap_usd / floor, 4),
            }
    return None


def cash_runway_quarters(row: dict, net_cash: float) -> Optional[float]:
    """Quarters of operating burn the net cash covers, or None if not burning.

    SF1 ARQ `ncfo` is one quarter's operating cash flow; negative = burning. A
    net-cash floor with a short runway is a MELTING floor (ARVN's caveat) — the
    caller flags it, the dossier stage prices it. None ⇒ cash-generative (no fuse)."""
    ncfo = _num(row, "ncfo")
    if ncfo >= 0:
        return None
    burn = -ncfo
    return round(max(net_cash, 0.0) / burn, 1)


def is_common_tradable(meta: dict) -> bool:
    """True if TICKERS metadata marks this a live common stock (or ADR) — not a
    warrant, preferred, unit, fund, ETN, or a delisted shell.

    REQUIRES a USD reporting currency (the FX-artifact guard): Sharadar's SF1
    balance sheet is in the filer's reporting currency, but the DAILY marketcap
    is USD. A KRW/CNY/JPY filer (GRVY, WIMI) shows a phantom ~100% "discount"
    purely because 616 billion KRW of book compared against a $456M USD cap. Only
    same-currency names produce a real floor-vs-price comparison."""
    if meta.get("isdelisted") != "N":
        return False
    if (meta.get("currency") or "USD") != "USD":
        return False
    cat = (meta.get("category") or "")
    if "Warrant" in cat:
        return False
    if (meta.get("sector") or "") in EXCLUDE_SECTORS:
        return False
    if (meta.get("industry") or "") in EXCLUDE_INDUSTRIES:
        return False
    return any(cat.startswith(p) for p in _COMMON_PREFIXES)


def screen_name(
    row: dict, mcap_usd: float, meta: dict, *,
    neglect_cap_usd: float = NEGLECT_CAP_USD,
    min_cap_usd: float = MIN_CAP_USD,
) -> Optional[dict]:
    """Screen ONE name → a neglect sourcing candidate, or None if it doesn't sit
    below a real floor in the coverage window. Pure: `row` is the latest SF1
    balance sheet, `mcap_usd` the current marketcap in dollars, `meta` the
    TICKERS row. Emits a candidate tagged `why_mispriced_type='neglect'` with the
    floor_basis the verification gate consumes."""
    if not is_common_tradable(meta):
        return None
    if not (min_cap_usd <= mcap_usd <= neglect_cap_usd):
        return None
    fl = floors(row)
    hit = best_floor(mcap_usd, fl)
    if hit is None:
        return None
    runway = cash_runway_quarters(row, fl.net_cash)
    eroding = runway is not None and runway < MIN_RUNWAY_Q
    return {
        "ticker": row.get("ticker"),
        "company": meta.get("name"),
        "sector": meta.get("sector"),
        "exchange": meta.get("exchange"),
        "why_mispriced_type": "neglect",
        "floor_type": hit["floor_type"],
        "floor_basis": hit["floor_basis"],
        "floor_usd": round(hit["floor_usd"], 0),
        "marketcap_usd": round(mcap_usd, 0),
        "discount": hit["discount"],
        "net_cash_usd": round(fl.net_cash, 0),
        "ncav_usd": round(fl.ncav, 0),
        "tangible_book_usd": round(fl.tangible_book, 0),
        "runway_quarters": runway,
        "eroding_floor": eroding,
        "as_of": row.get("datekey"),
        "source": "neglect_screen",
        "mechanism": ("Structural neglect: an uncovered small-cap priced below a "
                      "countable balance-sheet floor — no analyst, no index, no "
                      "forced buyer to close the gap."),
    }


def screen_panel(
    sf1_by_ticker: dict[str, dict],
    mcap_by_ticker: dict[str, float],
    meta_by_ticker: dict[str, dict],
    *,
    neglect_cap_usd: float = NEGLECT_CAP_USD,
    min_cap_usd: float = MIN_CAP_USD,
    exclude_tickers: Optional[set[str]] = None,
) -> list[dict]:
    """Run the screen across the whole panel → candidates, deepest discount first.

    `sf1_by_ticker` is one (latest) balance sheet per ticker, `mcap_by_ticker`
    the current marketcap in DOLLARS (caller converts Sharadar's $M), and
    `meta_by_ticker` the TICKERS metadata. `exclude_tickers` skips names already
    in the pool/pipeline so the screen surfaces only what's NEW."""
    exclude = exclude_tickers or set()
    out: list[dict] = []
    for ticker, row in sf1_by_ticker.items():
        if ticker in exclude:
            continue
        mcap = mcap_by_ticker.get(ticker)
        meta = meta_by_ticker.get(ticker)
        if mcap is None or meta is None:
            continue
        cand = screen_name(row, mcap, meta,
                           neglect_cap_usd=neglect_cap_usd, min_cap_usd=min_cap_usd)
        if cand:
            out.append(cand)
    return sorted(out, key=lambda c: -c["discount"])
