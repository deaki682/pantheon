"""Robinhood broker client for standalone Python use.

Wraps robin_stocks so the Achilles monitor (and other gods) can fetch
quotes and place orders without the MCP layer.

Authentication (env vars):
    ROBINHOOD_EMAIL       — Robinhood account email
    ROBINHOOD_PASSWORD    — Robinhood account password
    ROBINHOOD_TOTP_SECRET — (optional) TOTP base32 secret for automated MFA
    ROBINHOOD_PICKLE_PATH — (optional) session token directory (default ~/.tokens)

After first interactive login, robin_stocks caches a session token.
Subsequent runs reuse it automatically — no MFA prompt.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

log = logging.getLogger("shared.broker")

_logged_in = False
_account_number: Optional[str] = None


def _patch_imports():
    """robin_stocks imports tda/gemini subpackages which need cryptography.
    Stub them out — we only use the robinhood subpackage."""
    sys.modules.setdefault("robin_stocks.tda", type(sys)("stub"))
    sys.modules.setdefault("robin_stocks.gemini", type(sys)("stub"))


def login(*, force: bool = False) -> bool:
    """Authenticate with Robinhood. Returns True on success.

    Uses cached session tokens when available. Set force=True to
    re-authenticate even if already logged in.
    """
    global _logged_in, _account_number
    if _logged_in and not force:
        return True

    _patch_imports()
    try:
        from robin_stocks.robinhood import authentication
    except ImportError:
        log.warning("robin_stocks not installed — broker unavailable")
        return False

    email = os.environ.get("ROBINHOOD_EMAIL", "")
    password = os.environ.get("ROBINHOOD_PASSWORD", "")
    if not email or not password:
        log.info("ROBINHOOD_EMAIL/PASSWORD not set — broker unavailable")
        return False

    totp_secret = os.environ.get("ROBINHOOD_TOTP_SECRET", "")
    pickle_path = os.environ.get("ROBINHOOD_PICKLE_PATH", "")

    kwargs: dict = {
        "username": email,
        "password": password,
        "store_session": True,
        "expiresIn": 86400 * 7,
    }
    if pickle_path:
        kwargs["pickle_path"] = pickle_path
    if totp_secret:
        try:
            import pyotp
            kwargs["mfa_code"] = pyotp.TOTP(totp_secret).now()
        except ImportError:
            log.warning("pyotp not installed — cannot generate TOTP code")

    try:
        result = authentication.login(**kwargs)
        if result:
            _logged_in = True
            log.info("Robinhood authenticated as %s", email)
            return True
        log.error("Robinhood login returned falsy result")
        return False
    except Exception as exc:
        log.error("Robinhood login failed: %s", exc)
        return False


def logout():
    global _logged_in
    if not _logged_in:
        return
    _patch_imports()
    try:
        from robin_stocks.robinhood import authentication
        authentication.logout()
    except Exception:
        pass
    _logged_in = False


# ── quotes ─────────────────────────────────────────────────────────────

def get_quotes(symbols: list[str]) -> dict[str, float]:
    """Fetch current prices. Returns {SYMBOL: last_trade_price}."""
    if not symbols or not login():
        return {}
    _patch_imports()
    from robin_stocks.robinhood import stocks

    out: dict[str, float] = {}
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            results = stocks.get_quotes(batch) or []
            for row in results:
                if not row:
                    continue
                sym = (row.get("symbol") or "").upper()
                price_str = row.get("last_trade_price") or row.get("last_extended_hours_trade_price")
                if sym and price_str:
                    try:
                        out[sym] = float(price_str)
                    except (TypeError, ValueError):
                        pass
        except Exception as exc:
            log.warning("Quote batch failed (%d symbols): %s", len(batch), exc)
    return out


def get_latest_prices(symbols: list[str]) -> dict[str, float]:
    """Simpler price-only fetch (no bid/ask/volume)."""
    if not symbols or not login():
        return {}
    _patch_imports()
    from robin_stocks.robinhood import stocks

    out: dict[str, float] = {}
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            prices = stocks.get_latest_price(batch, includeExtendedHours=True) or []
            for sym, px in zip(batch, prices):
                if px is not None:
                    try:
                        out[sym.upper()] = float(px)
                    except (TypeError, ValueError):
                        pass
        except Exception as exc:
            log.warning("Price batch failed: %s", exc)
    return out


def get_fundamentals(symbols: list[str]) -> dict[str, dict]:
    """Fetch fundamentals (market_cap, pe_ratio, etc.)."""
    if not symbols or not login():
        return {}
    _patch_imports()
    from robin_stocks.robinhood import stocks

    out: dict[str, dict] = {}
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            results = stocks.get_fundamentals(batch) or []
            for sym, row in zip(batch, results):
                if row:
                    out[sym.upper()] = row
        except Exception as exc:
            log.warning("Fundamentals batch failed: %s", exc)
    return out


def get_market_caps(symbols: list[str]) -> dict[str, float]:
    """Fetch market caps only. Convenience wrapper around get_fundamentals."""
    fundies = get_fundamentals(symbols)
    out: dict[str, float] = {}
    for sym, data in fundies.items():
        mc = data.get("market_cap")
        if mc is not None:
            try:
                out[sym] = float(mc)
            except (TypeError, ValueError):
                pass
    return out


# ── orders ─────────────────────────────────────────────────────────────

def buy_fractional(
    symbol: str,
    dollars: float,
    *,
    account_number: Optional[str] = None,
) -> Optional[dict]:
    """Place a fractional-share market buy for a dollar amount."""
    if not login():
        return None
    _patch_imports()
    from robin_stocks.robinhood import orders

    acct = account_number or _account_number
    try:
        result = orders.order_buy_fractional_by_price(
            symbol, dollars,
            account_number=acct,
            timeInForce="gfd",
        )
        if isinstance(result, dict) and result.get("id"):
            log.info("BUY %s $%.2f → order %s", symbol, dollars, result["id"])
            return result
        log.warning("BUY %s $%.2f → unexpected: %s", symbol, dollars, result)
        return result if isinstance(result, dict) else None
    except Exception as exc:
        log.error("BUY %s $%.2f failed: %s", symbol, dollars, exc)
        return None


def sell_fractional(
    symbol: str,
    quantity: float,
    *,
    account_number: Optional[str] = None,
) -> Optional[dict]:
    """Place a fractional-share market sell for a share quantity."""
    if not login():
        return None
    _patch_imports()
    from robin_stocks.robinhood import orders

    acct = account_number or _account_number
    try:
        result = orders.order_sell_fractional_by_quantity(
            symbol, quantity,
            account_number=acct,
            timeInForce="gfd",
        )
        if isinstance(result, dict) and result.get("id"):
            log.info("SELL %s %.4f sh → order %s", symbol, quantity, result["id"])
            return result
        log.warning("SELL %s %.4f sh → unexpected: %s", symbol, quantity, result)
        return result if isinstance(result, dict) else None
    except Exception as exc:
        log.error("SELL %s %.4f sh failed: %s", symbol, quantity, exc)
        return None


# ── account ────────────────────────────────────────────────────────────

def get_holdings() -> dict[str, dict]:
    """Get current positions. Returns {SYMBOL: {price, quantity, equity, ...}}."""
    if not login():
        return {}
    _patch_imports()
    from robin_stocks.robinhood import account

    try:
        return account.build_holdings() or {}
    except Exception as exc:
        log.error("Holdings fetch failed: %s", exc)
        return {}


def get_account_cash() -> Optional[float]:
    """Get available cash in the account."""
    if not login():
        return None
    _patch_imports()
    from robin_stocks.robinhood import account

    try:
        profile = account.build_user_profile()
        if profile and "cash" in profile:
            return float(profile["cash"])
    except Exception as exc:
        log.error("Account cash fetch failed: %s", exc)
    return None
