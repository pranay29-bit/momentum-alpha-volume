"""
scanner/nse_client.py
---------------------
Handles fetching market-cap, free-float, and traded-value data.
Switched from NSE API to yfinance to bypass 401/403 Akamai blocks.
"""

from __future__ import annotations

import time
import logging

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_EMPTY = {
    "total_market_cap_cr": np.nan,
    "ff_pct":              np.nan,
    "traded_value_cr":     np.nan,
    "traded_volume":       np.nan,
    "traded_val_pct_of_ff": np.nan,
    "_ff_mc_raw":          np.nan,
}

def fetch_market_cap(symbol_ns: str) -> dict:
    """
    Fetch trade-info for a single symbol using yfinance.
    Converts raw Yahoo values to ₹ Crores to match the original NSE data structure.
    """
    try:
        ticker = yf.Ticker(symbol_ns)
        info = ticker.info
        
        # Extract raw data from Yahoo Finance
        market_cap_raw = info.get('marketCap')
        float_shares   = info.get('floatShares')
        current_price  = info.get('currentPrice') or info.get('regularMarketPrice')
        volume         = info.get('volume') or info.get('regularMarketVolume')

        # 1 Crore = 10,000,000
        total_mc_cr = (market_cap_raw / 10_000_000.0) if market_cap_raw else np.nan
        
        # Calculate Free Float
        ff_mc_raw = np.nan
        ff_mc_cr  = np.nan
        ff_pct    = np.nan
        
        if float_shares and current_price:
            ff_mc_raw = float_shares * current_price
            ff_mc_cr  = ff_mc_raw / 10_000_000.0
            if market_cap_raw:
                ff_pct = (ff_mc_raw / market_cap_raw) * 100.0

        # Calculate Traded Value
        traded_value_raw = np.nan
        traded_value_cr  = np.nan
        traded_val_pct_of_ff = np.nan
        
        if volume and current_price:
            traded_value_raw = volume * current_price
            traded_value_cr  = traded_value_raw / 10_000_000.0
            if not np.isnan(ff_mc_raw) and ff_mc_raw > 0:
                traded_val_pct_of_ff = (traded_value_raw / ff_mc_raw) * 100.0

        def _round(v, n=2):
            return round(v, n) if not np.isnan(v) else np.nan

        return {
            "total_market_cap_cr":  _round(total_mc_cr),
            "ff_pct":               _round(ff_pct),
            "traded_value_cr":      _round(traded_value_cr),
            "traded_volume":        volume if volume else np.nan,
            "traded_val_pct_of_ff": _round(traded_val_pct_of_ff, 4),
            "_ff_mc_raw":           _round(ff_mc_raw),
        }

    except Exception as exc:
        logger.error("yfinance fetch error for %s: %s", symbol_ns, exc)
        return _EMPTY.copy()

def enrich_with_market_caps(passing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add market-cap / liquidity columns to *passing_df* in-place (copy).
    Iterates symbols using yfinance.
    """
    if passing_df.empty:
        return passing_df

    logger.info("Fetching Market Cap data via yfinance for %d stocks…", len(passing_df))

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
        caps = fetch_market_cap(sym)
        for key in cols:
            cols[key].append(caps.get(key, np.nan))
            
        # A small delay is still good practice to avoid rate-limiting from Yahoo
        time.sleep(0.2) 

    out = passing_df.copy()
    for key, values in cols.items():
        out[key] = values

    # Calculate Liquidity Score
    ff_mc_s = pd.Series(cols["_ff_mc_raw"])
    tv_s    = pd.Series(cols["traded_value_cr"])
    out["liquidity_score"] = (tv_s.values / ff_mc_s.values)

    return out
