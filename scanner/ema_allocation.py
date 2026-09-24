"""
scanner/ema_allocation.py
--------------------------
EMA-Based Allocation Model (per "Implanting the DNA of a Successful Trader",
slide 47/48 — "EMA-Based Allocation Model" / "Rules for EMA Analysis").

For each index, CMP is compared against EMA21 / EMA50 / EMA100, and the EMAs
are compared against each other. Each comparison scores +1 or -1; the six
scores are summed into a single trend-strength score in the range [-6, +6],
which is then mapped onto a suggested allocation percentage.

Scoring rules (from the slide):
    1. Price  > EMA21   → +1   else -1
    2. Price  > EMA50   → +1   else -1
    3. Price  > EMA100  → +1   else -1
    4. EMA21  > EMA100  → +1   else -1
    5. EMA21  > EMA50   → +1   else -1
    6. EMA50  > EMA100  → +1   else -1

NOTE: the slide's bullet list has an apparent typo ("If EMA 50 > 50 EMA")
for rule 6 — read here as EMA50 vs EMA100, matching the "three EMAs compared
pairwise" structure described in the slide's own intro paragraph.

2-Candle Rule — SEPARATE from the score above, not part of it
---------------------------------------------------------------
From the whiteboard ("Sentiment / Sector / Stocks"), comparing the latest
daily candle (candle 2: H2/L2/C) against the one before it (candle 1: H1/L1):
    Bullish: H2 > H1  AND  L2 > L1  AND  C  > H1
    Bearish: L2 < L1  AND  H2 < H1  AND  C  < L1
    Otherwise: Neutral (most days satisfy neither pattern)

This is reported as its own "two_candle_signal" ("Bullish" / "Bearish" /
"Neutral") alongside the score and allocation %, but does NOT add ±1 into
the score and does NOT affect the -6..+6 range or the allocation % mapping.
It's a separate read on price action, shown side by side with the EMA-based
score rather than blended into it.

The score → allocation % mapping is NOT specified on the slide itself (it
only states "positive score = bullish, negative score = bearish"), so a
graduated table is used here. Adjust `SCORE_ALLOCATION_TABLE` below to match
your own house rules if you have a specific mapping in mind.
"""

from __future__ import annotations

import datetime as dt
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Indices to track ────────────────────────────────────────────────────────
# key → {
#   name           : display name
#   group          : "Broad Market" | "Market Cap"   (informational)
#   nse_symbol     : jugaad-data index_raw symbol (niftyindices.com), or None
#                    for indices niftyindices.com doesn't publish (BSE indices)
#   yf_candidates  : yfinance tickers tried in order if jugaad-data has no data
# }
#
# NOTE: yfinance tickers for the newer NSE indices are not stable — verify them
# with a quick `yf.download(ticker, period="1y")` and edit here if one returns
# empty. jugaad-data is tried first for every NSE index, so a stale yfinance
# ticker only matters when niftyindices.com is unreachable.
INDEX_DEFINITIONS: dict[str, dict] = {
    # ── Broad Market ───────────────────────────────────────────────────────
    "nifty50": {
        "name": "Nifty 50", "group": "Broad Market",
        "nse_symbol": "NIFTY 50",
        "yf_candidates": ["^NSEI"],
    },
    "niftynext50": {
        "name": "Nifty Next 50", "group": "Broad Market",
        "nse_symbol": "NIFTY NEXT 50",
        "yf_candidates": ["^NSMIDCP"],
    },
    "nifty100": {
        "name": "Nifty 100", "group": "Broad Market",
        "nse_symbol": "NIFTY 100",
        "yf_candidates": ["^CNX100"],
    },
    "nifty200": {
        "name": "Nifty 200", "group": "Broad Market",
        "nse_symbol": "NIFTY 200",
        "yf_candidates": ["^CNX200"],
    },
    "nifty500": {
        "name": "Nifty 500", "group": "Broad Market",
        "nse_symbol": "NIFTY 500",
        "yf_candidates": ["^CRSLDX"],
    },
    # ── Market-Cap Segments ────────────────────────────────────────────────
    "niftymidcap150": {
        "name": "Nifty Midcap 150", "group": "Market Cap",
        "nse_symbol": "NIFTY MIDCAP 150",
        "yf_candidates": ["NIFTYMIDCAP150.NS"],
    },
    "niftysmallcap250": {
        "name": "Nifty Smallcap 250", "group": "Market Cap",
        "nse_symbol": "NIFTY SMALLCAP 250",
        "yf_candidates": ["NIFTYSMLCAP250.NS", "^NSMIDCP250"],
    },
    "niftymicrocap250": {
        "name": "Nifty Microcap 250", "group": "Market Cap",
        "nse_symbol": "NIFTY MICROCAP 250",
        "yf_candidates": ["NIFTY_MICROCAP250.NS"],
    },
}

EMA_SPANS = {"EMA21": 21, "EMA50": 50, "EMA100": 100}

# score (sum of six ±1 EMA rules, range -6..+6) → suggested allocation %
# The 2-candle rule is intentionally NOT part of this sum — see module
# docstring. It's reported separately as two_candle_signal.
# Adjust freely — this is a reasonable graduated default, not from the slide.
SCORE_ALLOCATION_TABLE = [
    (6,  100),
    (4,  75),
    (2,  50),
    (0,  25),
    (-2, 10),
    (-4, 5),
    (-6, 0),
]


def _score_to_allocation(score: int) -> int:
    """Map a -6..+6 score onto an allocation % using SCORE_ALLOCATION_TABLE."""
    for threshold, pct in SCORE_ALLOCATION_TABLE:
        if score >= threshold:
            return pct
    return 0


def _fetch_index_ohlc(nse_symbol: str | None, yf_candidates: list[str]) -> pd.DataFrame | None:
    """
    Fetch ~260 trading days of daily OHLC (open/high/low/close) prices for an
    NSE index. Tries jugaad-data (niftyindices.com) first, then yfinance
    candidates. Mirrors the fetch pattern used in
    indicators.get_market_sentiment(). Returns a DataFrame with (at least)
    "close", "high", "low" columns, date-indexed and ascending, or None.

    High/Low are needed for the 2-candle rule (see module docstring), on top
    of Close which is all the EMA rules need.
    """
    ohlc: pd.DataFrame | None = None

    # ── 1. jugaad-data (skipped for BSE indices: nse_symbol is None) ────────
    try:
        if not nse_symbol:
            raise LookupError("no niftyindices.com symbol — going straight to yfinance")
        from jugaad_data.nse import index_raw
        to_date   = dt.date.today()
        from_date = to_date - dt.timedelta(days=260)  # comfortably > 100 EMA warm-up
        records   = index_raw(symbol=nse_symbol, from_date=from_date, to_date=to_date)
        if records:
            tmp = pd.DataFrame(records)
            date_col  = next((c for c in tmp.columns if "date" in c.lower()), None)
            close_col = next((c for c in tmp.columns if "close" in c.lower()), None)
            high_col  = next((c for c in tmp.columns if "high" in c.lower()), None)
            low_col   = next((c for c in tmp.columns if c.lower().startswith("low") or c.lower() == "low"), None)
            if date_col and close_col and high_col and low_col:
                tmp[date_col] = pd.to_datetime(tmp[date_col], dayfirst=True, errors="coerce")
                for c in (close_col, high_col, low_col):
                    tmp[c] = pd.to_numeric(tmp[c].astype(str).str.replace(",", ""), errors="coerce")
                tmp = tmp.dropna(subset=[date_col, close_col, high_col, low_col]).sort_values(date_col)
                if len(tmp) >= 101:
                    ohlc = tmp.set_index(date_col)[[close_col, high_col, low_col]].astype(float)
                    ohlc.columns = ["close", "high", "low"]
                    logger.info("[EMA Allocation] jugaad-data OK for %s — %d rows", nse_symbol, len(ohlc))
    except Exception as exc:
        logger.info("[EMA Allocation] jugaad-data skipped/failed for %s: %s", nse_symbol, exc)

    # ── 2. yfinance fallback ────────────────────────────────────────────────
    if ohlc is None:
        import yfinance as yf
        for ticker in yf_candidates:
            try:
                raw = yf.download(
                    ticker, period="1y", interval="1d",
                    progress=False, auto_adjust=True, threads=False,
                )
                if raw is None or raw.empty:
                    continue
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.get_level_values(0)
                sub = raw[["Close", "High", "Low"]].dropna()
                if len(sub) >= 101:
                    ohlc = sub.astype(float)
                    ohlc.columns = ["close", "high", "low"]
                    logger.info("[EMA Allocation] yfinance %s OK — %d rows", ticker, len(sub))
                    break
            except Exception as exc:
                logger.warning("[EMA Allocation] yfinance %s failed: %s", ticker, exc)

    return ohlc


def compute_ema_allocation_for_index(key: str, history_days: int = 20) -> dict:
    """
    Fetch data and compute the EMA-based allocation score for a single index.
    Returns a dict with close/EMA values, per-rule scores, total score,
    signal label, suggested allocation %, and a `history` list containing the
    same (date, score, allocation_pct) for each of the last `history_days`
    trading days. Gracefully degrades to an "unavailable" dict if data can't
    be fetched.
    """
    meta = INDEX_DEFINITIONS[key]
    result: dict = {
        "key": key,
        "name": meta["name"],
        "group": meta.get("group", ""),
        "available": False,
        "close": None,
        "ema21": None, "ema50": None, "ema100": None,
        "rules": {},
        "score": None,
        "signal": "unavailable",
        "allocation_pct": None,
        "two_candle_rule": None,
        "two_candle_signal": "unavailable",
        "as_of": None,
        "history": [],
    }

    ohlc = _fetch_index_ohlc(meta["nse_symbol"], meta["yf_candidates"])
    if ohlc is None or len(ohlc) < 101:
        logger.warning("[EMA Allocation] No usable data for %s", meta["name"])
        return result

    close_series = ohlc["close"]
    high_series  = ohlc["high"]
    low_series   = ohlc["low"]

    ema21  = close_series.ewm(span=EMA_SPANS["EMA21"],  adjust=False).mean()
    ema50  = close_series.ewm(span=EMA_SPANS["EMA50"],  adjust=False).mean()
    ema100 = close_series.ewm(span=EMA_SPANS["EMA100"], adjust=False).mean()

    # Vectorized per-day scores across the whole series, so we can slice the
    # last N days for history without recomputing EMAs per-day.
    # 2-candle rule (see module docstring): compare each day's candle (H2/L2/C)
    # against the prior day's candle (H1/L1). Bullish +1 / bearish -1 / else 0
    # — unlike the six EMA rules, most days trigger neither pattern.
    prev_high = high_series.shift(1)
    prev_low  = low_series.shift(1)
    two_candle_bullish = (high_series > prev_high) & (low_series > prev_low) & (close_series > prev_high)
    two_candle_bearish = (low_series < prev_low) & (high_series < prev_high) & (close_series < prev_low)
    two_candle_rule = np.select([two_candle_bullish, two_candle_bearish], [1, -1], default=0)

    rules_df = pd.DataFrame({
        "price_above_ema21":  np.where(close_series > ema21,  1, -1),
        "price_above_ema50":  np.where(close_series > ema50,  1, -1),
        "price_above_ema100": np.where(close_series > ema100, 1, -1),
        "ema21_above_ema100": np.where(ema21 > ema100, 1, -1),
        "ema21_above_ema50":  np.where(ema21 > ema50,  1, -1),
        "ema50_above_ema100": np.where(ema50 > ema100, 1, -1),
    }, index=close_series.index)
    daily_score = rules_df.sum(axis=1)
    daily_alloc = daily_score.apply(_score_to_allocation)

    # two_candle_rule stays OUT of rules_df / daily_score on purpose — it's
    # reported as its own signal, not blended into the -6..+6 score.
    two_candle_series = pd.Series(two_candle_rule, index=close_series.index)

    def _two_candle_label(v: int) -> str:
        return "Bullish" if v > 0 else "Bearish" if v < 0 else "Neutral"

    price   = float(close_series.iloc[-1])
    e21     = float(ema21.iloc[-1])
    e50     = float(ema50.iloc[-1])
    e100    = float(ema100.iloc[-1])
    as_of   = close_series.index[-1]

    rules = {col: int(rules_df[col].iloc[-1]) for col in rules_df.columns}
    score = int(daily_score.iloc[-1])
    two_candle_value = int(two_candle_series.iloc[-1])
    two_candle_signal = _two_candle_label(two_candle_value)

    if score > 0:
        signal = "bullish"
    elif score < 0:
        signal = "bearish"
    else:
        signal = "neutral"

    history = [
        {
            "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
            "score": int(daily_score.loc[idx]),
            "allocation_pct": int(daily_alloc.loc[idx]),
            "two_candle_rule": int(two_candle_series.loc[idx]),
            "two_candle_signal": _two_candle_label(int(two_candle_series.loc[idx])),
        }
        for idx in close_series.index[-history_days:]
    ]

    result.update({
        "available": True,
        "close": round(price, 2),
        "ema21": round(e21, 2),
        "ema50": round(e50, 2),
        "ema100": round(e100, 2),
        "rules": rules,
        "score": score,
        "signal": signal,
        "allocation_pct": _score_to_allocation(score),
        # Separate from score/allocation above — see module docstring.
        "two_candle_rule": two_candle_value,
        "two_candle_signal": two_candle_signal,
        "as_of": as_of.strftime("%Y-%m-%d") if hasattr(as_of, "strftime") else str(as_of),
        "history": history,
    })
    return result


def compute_ema_allocation_all(history_days: int = 20) -> dict[str, dict]:
    """Compute the EMA-based allocation result (with history) for every index in INDEX_DEFINITIONS."""
    return {key: compute_ema_allocation_for_index(key, history_days=history_days) for key in INDEX_DEFINITIONS}
