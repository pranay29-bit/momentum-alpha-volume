"""
scanner/breakdown_stocks.py
-----------------------------
"Breakdown Stocks" scan — large-cap stocks that were recently in the
Momentum dashboard (cleared all 8 Trend Template conditions within the
last `lookback_days` calendar days) but whose price has since fallen
back below its 50-day moving average today.

Cond5 of the Trend Template ("price above MA50") is the first, fastest
support level to break when a leader starts running out of steam — so a
stock that recently qualified for Momentum and has now cracked its 50-day
line is a legitimate early-warning signal, especially at large market
caps where institutional participation is heaviest and a broken 50-day
line often marks real distribution, not noise.

This is the mirror image of scanner.new_rs_high — that scan looks for
strength emerging early; this one looks for recently-confirmed strength
breaking down. Both reconstruct history from the same daily archive, no
new data source.

Only stocks with market cap >= `min_market_cap_cr` (₹50,000 Cr by
default — large/mega-cap territory) are included, since this dashboard
is specifically meant as a risk radar for big, liquid, widely-held names,
not noise from illiquid small caps whipsawing around their 50-day line.

Public entry point:

    compute_breakdown_stocks(df, docs_dir, today_str, lookback_days=10,
                              min_market_cap_cr=50000.0)
        -> pd.DataFrame (subset of df that recently passed Momentum and
           is now below its 50-day MA, enriched with market-cap data and
           filtered to the cap floor)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LOOKBACK_DAYS      = 10        # matches the site-wide "✦ NEW (10-day)" convention
MIN_MARKET_CAP_CR  = 50_000.0  # large/mega-cap floor


def _load_recent_momentum_symbols(
    docs_dir: str | Path,
    today_str: str,
    lookback_days: int = LOOKBACK_DAYS,
) -> dict[str, str]:
    """
    Scan the last `lookback_days` calendar days of archived
    `passing_stocks_<date>.csv` files (the Momentum dashboard's own output
    — not Elite, not Volume Action) and return {symbol: most_recent_date_seen}
    for every symbol that appeared at least once.
    """
    docs_root = Path(docs_dir)
    if not docs_root.exists():
        return {}

    today_date = datetime.strptime(today_str, "%Y%m%d").date()
    last_seen: dict[str, str] = {}

    for d in sorted(docs_root.iterdir(), key=lambda p: p.name):
        if not (d.is_dir() and d.name.replace("-", "").isdigit() and len(d.name.replace("-", "")) == 8):
            continue
        slug = d.name.replace("-", "")
        if slug == today_str:
            continue
        try:
            dir_date = datetime.strptime(slug, "%Y%m%d").date()
        except ValueError:
            continue
        if (today_date - dir_date).days > lookback_days:
            continue

        csv_path = d / f"passing_stocks_{slug}.csv"
        if not csv_path.exists():
            continue
        try:
            day_df = pd.read_csv(csv_path, usecols=lambda c: c == "symbol")
        except Exception as exc:
            logger.debug("Could not read %s: %s", csv_path, exc)
            continue
        for sym in day_df.get("symbol", pd.Series(dtype=str)).dropna():
            sym = str(sym)
            # Track the most recent date each symbol was seen passing.
            if sym not in last_seen or slug > last_seen[sym]:
                last_seen[sym] = slug

    return last_seen


def compute_breakdown_stocks(
    df: pd.DataFrame,
    docs_dir: str | Path,
    today_str: str,
    lookback_days: int = LOOKBACK_DAYS,
    min_market_cap_cr: float = MIN_MARKET_CAP_CR,
    enrich_fn=None,
) -> pd.DataFrame:
    """
    Return large-cap stocks that were in the Momentum dashboard within the
    last `lookback_days` days but are trading below their 50-day MA today.

    `enrich_fn` defaults to `scanner.nse_client.enrich_with_market_caps`
    (imported lazily to avoid a hard dependency at module load, and to
    make this trivially testable with a stub).
    """
    if df is None or df.empty:
        return pd.DataFrame()
    required = {"symbol", "close", "MA50", "cond5_price_above_ma50"}
    if not required.issubset(df.columns):
        logger.warning("Breakdown scan skipped — missing columns: %s", required - set(df.columns))
        return pd.DataFrame()

    recent = _load_recent_momentum_symbols(docs_dir, today_str, lookback_days)
    if not recent:
        logger.info("Breakdown scan: no symbols passed Momentum in the last %d days.", lookback_days)
        return pd.DataFrame()

    candidates = df[
        df["symbol"].isin(recent.keys()) & (df["cond5_price_above_ma50"] == False)  # noqa: E712
    ].copy()

    if candidates.empty:
        logger.info("Breakdown scan: %d recently-passing symbols, none currently below MA50.", len(recent))
        return pd.DataFrame()

    candidates["last_passing_date"] = candidates["symbol"].map(recent)
    candidates["pct_below_ma50"] = (
        (candidates["close"].astype(float) - candidates["MA50"].astype(float))
        / candidates["MA50"].astype(float) * 100.0
    )

    if enrich_fn is None:
        from .nse_client import enrich_with_market_caps as enrich_fn

    enriched = enrich_fn(candidates)

    if "total_market_cap_cr" not in enriched.columns:
        logger.warning("Breakdown scan: market-cap enrichment returned no data — cannot apply the cap floor.")
        return pd.DataFrame()

    out = enriched[enriched["total_market_cap_cr"] >= min_market_cap_cr].copy()
    out = out.sort_values("pct_below_ma50", ascending=True).reset_index(drop=True)  # worst breaks first

    logger.info(
        "Breakdown Stocks: %d/%d recently-passing large-caps (≥ ₹%.0f Cr) now below MA50.",
        len(out), len(recent), min_market_cap_cr,
    )
    return out
