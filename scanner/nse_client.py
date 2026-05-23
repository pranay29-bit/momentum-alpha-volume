"""
scanner/nse_client.py
---------------------
Handles all communication with the NSE India public API.
Fetches market-cap, free-float and traded-value data for each symbol.
"""

from __future__ import annotations

import time
import logging

import numpy as np
import pandas as pd
import requests

from .config import NSE_HEADERS, NSE_REQUEST_DELAY
from .utils  import safe_float

logger = logging.getLogger(__name__)

_EMPTY = {
    "total_market_cap_cr": np.nan,
    "ff_pct":              np.nan,
    "traded_value_cr":     np.nan,
    "traded_volume":       np.nan,
    "traded_val_pct_of_ff": np.nan,
    "_ff_mc_raw":          np.nan,
}


def create_session() -> requests.Session:
    """Return a warmed-up requests.Session with NSE cookies."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=15)
        time.sleep(1)
        logger.debug("NSE session initialised.")
    except Exception as exc:
        logger.warning("Could not initialise NSE session: %s", exc)
    return session


def fetch_market_cap(symbol_ns: str, session: requests.Session) -> dict:
    """
    Fetch trade-info for a single symbol from NSE's quote-equity API.

    Returns a dict with keys:
        total_market_cap_cr, ff_pct, traded_value_cr,
        traded_volume, traded_val_pct_of_ff, _ff_mc_raw
    """
    nse_sym = symbol_ns.replace(".NS", "").strip()
    encoded = nse_sym.replace("&", "%26").replace(" ", "%20")
    url = (
        f"https://www.nseindia.com/api/quote-equity"
        f"?symbol={encoded}&section=trade_info"
    )

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            logger.warning("NSE HTTP %s for %s", resp.status_code, nse_sym)
            return _EMPTY.copy()

        data       = resp.json()
        trade_info = data.get("marketDeptOrderBook", {}).get("tradeInfo", {})

        total_mc           = safe_float(trade_info.get("totalMarketCap"))
        ff_mc              = safe_float(trade_info.get("ffmc"))
        traded_value_cr    = safe_float(trade_info.get("totalTradedValue"))   # already in ₹ Cr
        traded_volume      = safe_float(trade_info.get("totalTradedVolume"))

        ff_pct             = np.nan
        if not np.isnan(total_mc) and total_mc > 0 and not np.isnan(ff_mc):
            ff_pct = (ff_mc / total_mc) * 100.0

        traded_pct_of_ff   = np.nan
        if not np.isnan(ff_mc) and ff_mc > 0 and not np.isnan(traded_value_cr):
            traded_pct_of_ff = (traded_value_cr / ff_mc) * 100.0

        def _round(v, n=2):
            return round(v, n) if not np.isnan(v) else np.nan

        return {
            "total_market_cap_cr":  _round(total_mc),
            "ff_pct":               _round(ff_pct),
            "traded_value_cr":      _round(traded_value_cr),
            "traded_volume":        traded_volume,
            "traded_val_pct_of_ff": _round(traded_pct_of_ff, 4),
            "_ff_mc_raw":           _round(ff_mc),
        }

    except Exception as exc:
        logger.error("NSE fetch error for %s: %s", nse_sym, exc)
        return _EMPTY.copy()


def enrich_with_market_caps(passing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add market-cap / liquidity columns to *passing_df* in-place (copy).
    Iterates symbols with a polite delay between requests.
    """
    if passing_df.empty:
        return passing_df

    logger.info("Fetching NSE data for %d stocks…", len(passing_df))
    session = create_session()

    cols: dict[str, list] = {
        "total_market_cap_cr":  [],
        "ff_pct":               [],
        "traded_value_cr":      [],
        "traded_volume":        [],
        "traded_val_pct_of_ff": [],
        "_ff_mc_raw":           [],
    }

    for i, sym in enumerate(passing_df["symbol"], start=1):
        logger.info("  [%d/%d] %s", i, len(passing_df), sym)
        caps = fetch_market_cap(sym, session)
        for key in cols:
            cols[key].append(caps.get(key, np.nan))
        time.sleep(NSE_REQUEST_DELAY)

    out = passing_df.copy()
    for key, values in cols.items():
        out[key] = values

    ff_mc_s = pd.Series(cols["_ff_mc_raw"])
    tv_s    = pd.Series(cols["traded_value_cr"])
    out["liquidity_score"] = (tv_s.values / ff_mc_s.values)

    return out
