"""Watchlist construction.

Built in source-priority order:
  1. activist 13D names (most recent)
  2. insider cluster names
  3. smart-money 13F holdings
  4. multi-lens screen survivors
  5. broad quality screen survivors
  6. fallback seed list (~83 curated names)

Capped at 800 names because SEC rate-limits ~10 req/s and Achilles needs
to complete a full poll within its cadence window.
"""
from __future__ import annotations

from typing import Iterable


WATCHLIST_CAP = 800


# A curated seed of neglected small/mid-cap names — the final fallback
# when all other sources fail. Long enough to provide coverage, short
# enough to be reviewable.
SEED_WATCHLIST = (
    "AOSL", "AMSC", "BANR", "BOX", "BRBR", "CABA", "CALX", "CASS", "CCSI",
    "CDXS", "CECO", "CETX", "CIFR", "CIVI", "CMTL", "CNDT", "CRAI", "CRGY",
    "CRMT", "CSBR", "CTSO", "CURI", "CXM", "CYRX", "DAKT", "DCO", "DGII",
    "DOCN", "DXPE", "EHTH", "EZPW", "FOXF", "GPRO", "GRPN", "HCAT", "HCKT",
    "HEAR", "HMHC", "HSII", "IBEX", "ICUI", "IIIN", "IIIV", "IIPR", "INSE",
    "JJSF", "KALU", "KAR", "KFY", "KNDI", "KOPN", "KRON", "LASR", "LIQT",
    "LMAT", "LMB", "LTRX", "LYTS", "MAXR", "MBII", "MCFE", "METC", "MGNI",
    "MITK", "MLAB", "MRCY", "MTRX", "NATH", "NGS", "NSSC", "NTGR", "NUVR",
    "NX", "OFIX", "OII", "OMCL", "PCYO", "PDFS", "PFGC", "PHIN", "PKE",
    "POWL", "POWW", "PRGS",
)


def build_watchlist(
    *,
    activist_13d: Iterable[str] = (),
    insider_clusters: Iterable[str] = (),
    smart_money: Iterable[str] = (),
    multi_lens: Iterable[str] = (),
    broad_screen: Iterable[str] = (),
    seed: Iterable[str] = SEED_WATCHLIST,
    cap: int = WATCHLIST_CAP,
) -> list[str]:
    """Compose the watchlist in priority order, dedup, cap at `cap`."""
    out: list[str] = []
    seen: set[str] = set()
    sources = (
        activist_13d, insider_clusters, smart_money,
        multi_lens, broad_screen, seed,
    )
    for src in sources:
        for sym in src or ():
            s = str(sym).upper().strip()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
            if len(out) >= cap:
                return out
    return out


def attribute_source(
    symbol: str, *,
    activist_13d: Iterable[str] = (),
    insider_clusters: Iterable[str] = (),
    smart_money: Iterable[str] = (),
    multi_lens: Iterable[str] = (),
    broad_screen: Iterable[str] = (),
    seed: Iterable[str] = SEED_WATCHLIST,
) -> str:
    """Return the highest-priority source that contributed this symbol."""
    s = symbol.upper().strip()
    for name, src in (
        ("activist_13d", activist_13d),
        ("insider_clusters", insider_clusters),
        ("smart_money", smart_money),
        ("multi_lens", multi_lens),
        ("broad_screen", broad_screen),
        ("seed", seed),
    ):
        if s in {str(x).upper().strip() for x in (src or ())}:
            return name
    return "unknown"
