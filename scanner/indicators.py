"""
scanner/indicators.py
---------------------
All technical-indicator computation and Minervini trend-template evaluation.
Each function is pure (takes a DataFrame, returns a value / dict / bool).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    MA12_WINDOW, MA36_WINDOW, MA50_WINDOW,
    MA150_WINDOW, MA200_WINDOW, EMA10_WINDOW, EMA20_WINDOW,
    RS_LOOKBACK,
)


# ── Indicator computation ─────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA/EMA and 52-week high/low columns to *df*. Returns a copy."""
    df = df.copy()
    df["MA12"]   = df["Close"].rolling(window=MA12_WINDOW).mean()
    df["MA36"]   = df["Close"].rolling(window=MA36_WINDOW).mean()
    df["MA50"]   = df["Close"].rolling(window=MA50_WINDOW).mean()
    df["MA150"]  = df["Close"].rolling(window=MA150_WINDOW).mean()
    df["MA200"]  = df["Close"].rolling(window=MA200_WINDOW).mean()
    df["EMA10"]  = df["Close"].ewm(span=EMA10_WINDOW, adjust=False).mean()
    df["EMA20"]  = df["Close"].ewm(span=EMA20_WINDOW, adjust=False).mean()
    df["52w_low"]  = df["Low"].rolling(window=RS_LOOKBACK).min()
    df["52w_high"] = df["High"].rolling(window=RS_LOOKBACK).max()
    df["inside_bar"] = (df["High"] < df["High"].shift(1)) & (df["Low"] > df["Low"].shift(1))  # ← ADD THIS
    return df

def get_market_sentiment(df: pd.DataFrame | None = None) -> dict:
    """
    Compute NSE market breadth sentiment from the scan results DataFrame.

    Rather than fetching index prices via Yahoo Finance (which fails silently
    when those specific tickers are unavailable), we derive sentiment directly
    from the EMA10 / EMA20 flags already computed for every stock in the scan.

    Returns two "panels" styled like the old index cards:
      • "All NSE"   — breadth across every stock in the scan universe
      • "Trend Pass" — breadth only across stocks that pass the Minervini
                       trend template (more refined signal)

    Each panel shows:
      • pct_above_ema10  / pct_above_ema20
      • above_ema10 / above_ema20 booleans (True = majority above)
    """
    empty = lambda name: {
        "close": None, "ema10": None, "ema20": None,
        "above_ema10": None, "above_ema20": None, "name": name,
        "pct_above_ema10": None, "pct_above_ema20": None,
        "count": 0,
    }

    result: dict = {
        "cnxsmallcap":    empty("NSE Breadth — All Stocks"),
        "niftysmlcap250": empty("NSE Breadth — Trend Template Stocks"),
        "overall": "unavailable",
    }

    if df is None or df.empty:
        return result

    try:
        # ── Panel 1: all stocks ───────────────────────────────────────────────
        ema10_col  = "cond9_price_above_ema10"   # pre-computed in indicators.py
        trend_col  = "trend_template_pass"        # True = passes all conditions

        total = len(df)
        if total == 0:
            return result

        # EMA10 above/below
        if ema10_col in df.columns:
            above10_all = df[ema10_col].sum()
            pct10_all   = round(100.0 * above10_all / total, 1)
        else:
            # Fallback: check if close > EMA10 column directly
            above10_all = 0
            pct10_all   = None

        # EMA20: derive from MA150 proxy or compute from close/MA columns
        # Use MA50 as a proxy for "above medium-term average" when EMA20 not stored
        ma50_col = "MA50"
        if ma50_col in df.columns:
            above20_all = (df["close"] > df[ma50_col]).sum() if "close" in df.columns else 0
            pct20_all   = round(100.0 * above20_all / total, 1)
        else:
            above20_all = 0
            pct20_all   = None

        result["cnxsmallcap"].update({
            "above_ema10":      bool(pct10_all is not None and pct10_all >= 50),
            "above_ema20":      bool(pct20_all is not None and pct20_all >= 50),
            "pct_above_ema10":  pct10_all,
            "pct_above_ema20":  pct20_all,
            "count":            total,
        })

        # ── Panel 2: trend-template stocks only ───────────────────────────────
        if trend_col in df.columns:
            df_trend = df[df[trend_col] == True]
        else:
            # Fall back to stocks passing at least 6 of 7 conditions
            cond_cols = [c for c in df.columns if c.startswith("cond") and df[c].dtype == bool]
            if cond_cols:
                df_trend = df[df[cond_cols].sum(axis=1) >= 6]
            else:
                df_trend = df.head(0)

        trend_total = len(df_trend)
        if trend_total > 0 and ema10_col in df_trend.columns:
            above10_tr  = df_trend[ema10_col].sum()
            pct10_tr    = round(100.0 * above10_tr / trend_total, 1)
            if ma50_col in df_trend.columns and "close" in df_trend.columns:
                above20_tr = (df_trend["close"] > df_trend[ma50_col]).sum()
                pct20_tr   = round(100.0 * above20_tr / trend_total, 1)
            else:
                above20_tr, pct20_tr = 0, None
            result["niftysmlcap250"].update({
                "above_ema10":      bool(pct10_tr >= 50),
                "above_ema20":      bool(pct20_tr is not None and pct20_tr >= 50),
                "pct_above_ema10":  pct10_tr,
                "pct_above_ema20":  pct20_tr,
                "count":            trend_total,
            })

        # ── Overall signal ────────────────────────────────────────────────────
        bull_count = 0
        ok_count   = 0
        for key in ("cnxsmallcap", "niftysmlcap250"):
            p = result[key]
            if p["pct_above_ema10"] is not None:
                ok_count += 1
                score = (1 if p["above_ema10"] else 0) + (0.5 if p["above_ema20"] else 0)
                bull_count += score

        if ok_count == 0:
            result["overall"] = "unavailable"
        elif bull_count >= ok_count * 0.75:
            result["overall"] = "bullish"
        elif bull_count <= ok_count * 0.25:
            result["overall"] = "bearish"
        else:
            result["overall"] = "mixed"

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Market sentiment computation failed: %s", exc)

    return result


# ── Helper predicates ─────────────────────────────────────────────────────────

def _strictly_increasing(series: pd.Series, days: int = 21) -> bool:
    s = series.dropna()
    if len(s) < days:
        return False
    return (s.tail(days).diff().dropna() > 0).all()


def _bullish_crossover_today(fast: pd.Series, slow: pd.Series) -> bool:
    """True iff fast crossed above slow on the most-recent bar."""
    idx = fast.dropna().index.intersection(slow.dropna().index)
    if len(idx) < 2:
        return False
    f, s = fast.loc[idx], slow.loc[idx]
    return bool((f.iloc[-1] > s.iloc[-1]) and (f.iloc[-2] <= s.iloc[-2]))


# ── 12-month relative-strength return ────────────────────────────────────────

def compute_12m_return(df: pd.DataFrame) -> float:
    if len(df) < RS_LOOKBACK + 1:
        return np.nan
    latest = df["Close"].iloc[-1]
    past   = df["Close"].iloc[-RS_LOOKBACK]
    if past == 0 or pd.isna(past):
        return np.nan
    return (latest / past - 1.0) * 100.0

def is_inside_candle(df: pd.DataFrame) -> bool:
    """
    Returns True if the latest bar is an inside candle
    (its high/low range is fully contained within the prior bar's range).
    """
    if len(df) < 2:
        return False
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    return bool((curr["High"] < prev["High"]) and (curr["Low"] > prev["Low"]))


# ── Minervini Trend Template ──────────────────────────────────────────────────

_TEMPLATE_DEFAULTS = {
    "close": np.nan,
    "MA12":  np.nan, "MA36":  np.nan, "MA50":  np.nan,
    "MA150": np.nan, "MA200": np.nan, "EMA10": np.nan,
    "52w_low": np.nan, "52w_high": np.nan,
    "cond1_price_above_150_200":   False,
    "cond2_ma150_above_ma200":     False,
    "cond3_ma200_trending_up_1m":  False,
    "cond4_ma50_above_150_200":    False,
    "cond5_price_above_ma50":      False,
    "cond6_30pct_above_52w_low":   False,
    "cond7_within_25pct_52w_high": False,
    "cond9_price_above_ema10":     False,
    "fresh_ma12_cross_today":      False,
}


def evaluate_trend_template(df: pd.DataFrame) -> dict:
    """
    Evaluate all Minervini trend-template conditions for the latest bar.
    Returns a flat dict; all booleans default to False on insufficient data.
    """
    result = dict(_TEMPLATE_DEFAULTS)
    if df.empty or len(df) < RS_LOOKBACK:
        return result

    row   = df.iloc[-1]
    close = row["Close"]

    vals = {k: row.get(k, np.nan) for k in
            ["MA12", "MA36", "MA50", "MA150", "MA200", "EMA10", "52w_low", "52w_high"]}

    result.update({"close": close, **vals})

    if any(pd.isna(v) for v in vals.values()):
        return result

    ma12, ma36   = vals["MA12"],  vals["MA36"]
    ma50         = vals["MA50"]
    ma150, ma200 = vals["MA150"], vals["MA200"]
    ema10        = vals["EMA10"]
    low_52w      = vals["52w_low"]
    high_52w     = vals["52w_high"]

    result.update({
        "cond1_price_above_150_200":   close > ma150 and close > ma200,
        "cond2_ma150_above_ma200":     ma150 > ma200,
        "cond3_ma200_trending_up_1m":  _strictly_increasing(df["MA200"], 21),
        "cond4_ma50_above_150_200":    ma50 > ma150 and ma50 > ma200,
        "cond5_price_above_ma50":      close > ma50,
        "cond6_30pct_above_52w_low":   close >= 1.30 * low_52w,
        "cond7_within_25pct_52w_high": close >= 0.75 * high_52w,
        "cond9_price_above_ema10":     close > ema10,
        "fresh_ma12_cross_today":      _bullish_crossover_today(df["MA12"], df["MA36"]),
    })
    return result


# ── Smart Volume / Pocket Pivot ──────────────────────────────────────────────

def compute_volume_action(df: pd.DataFrame) -> dict:
    """Compute latest-day volume action labels."""
    result = {
        "volume_signal": "noise",
        "relative_volume": np.nan,
        "bull_snort": False,
    }
    if df.empty or len(df) < 21:
        return result

    vol_ma = df["Volume"].rolling(50).mean()
    latest = df.iloc[-1]
    latest_close = latest["Close"]
    prev_close = df["Close"].iloc[-2]
    latest_vol = latest["Volume"]
    latest_vol_ma = vol_ma.iloc[-1]

    highest_down_volume = 0
    for i in range(max(0, len(df)-21), len(df)-1):
        if i <= 0:
            continue
        if df["Close"].iloc[i] < df["Close"].iloc[i-1]:
            highest_down_volume = max(highest_down_volume, df["Volume"].iloc[i])

    is_up_day = latest_close > prev_close
    is_down_day = latest_close < prev_close
    is_ppv = is_up_day and latest_vol > highest_down_volume

    volume_signal = 'noise'
    if is_ppv:
        volume_signal = 'ppv'
    elif is_up_day and latest_vol > latest_vol_ma:
        volume_signal = 'green'
    elif is_down_day and latest_vol > latest_vol_ma:
        volume_signal = 'red'
    elif latest_vol <= latest_vol_ma * 0.20:
        volume_signal = 'dry'

    candle_range = latest['High'] - latest['Low']
    close_position = ((latest_close - latest['Low']) / candle_range) if candle_range > 0 else 0

    result.update({
        'volume_signal': volume_signal,
        'relative_volume': (latest_vol / latest_vol_ma) * 100 if latest_vol_ma else np.nan,
        'bull_snort': bool((latest_vol >= 3 * latest_vol_ma) and (close_position >= 0.65) and is_up_day)
    })
    return result
