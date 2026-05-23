"""
scanner/data_loader.py
----------------------
Loads symbol list from CSV and downloads OHLCV data from Yahoo Finance
in configurable batches.
"""

from __future__ import annotations

import logging
from math import ceil
from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import (
    CSV_PATH, SYMBOL_COLUMN, EXCHANGE_SUFFIX,
    PERIOD, INTERVAL, BATCH_SIZE,
)
from .indicators import add_indicators, evaluate_trend_template, compute_12m_return, compute_volume_action

logger = logging.getLogger(__name__)


# ── Symbol list ───────────────────────────────────────────────────────────────

def load_symbols(csv_path: str = CSV_PATH, symbol_col: str = SYMBOL_COLUMN) -> list[str]:
    df  = pd.read_csv(csv_path)
    raw = df[symbol_col].dropna().astype(str).str.strip().unique().tolist()
    return [s if "." in s else s + EXCHANGE_SUFFIX for s in raw]


# ── Batch downloader ──────────────────────────────────────────────────────────

def _chunk(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def _process_symbol(sym: str, data: pd.DataFrame, is_multi: bool) -> dict | None:
    try:
        df_sym = data[sym].copy() if is_multi else data.copy()
        if "Close" not in df_sym.columns:
            if "Adj Close" in df_sym.columns:
                df_sym = df_sym.rename(columns={"Adj Close": "Close"})
            else:
                return None
        df_sym = df_sym.dropna(subset=["Close"])
        if df_sym.empty:
            return None

        df_sym  = add_indicators(df_sym)
        tpl     = evaluate_trend_template(df_sym)
        rs_ret  = compute_12m_return(df_sym)
        vol_data = compute_volume_action(df_sym)

        return {
            "symbol":  sym,
            "close":   tpl["close"],
            "MA12":    tpl["MA12"],  "MA36":  tpl["MA36"],
            "MA50":    tpl["MA50"],  "MA150": tpl["MA150"],
            "MA200":   tpl["MA200"], "EMA10": tpl["EMA10"],
            "52w_low":  tpl["52w_low"],
            "52w_high": tpl["52w_high"],
            "cond1_price_above_150_200":   tpl["cond1_price_above_150_200"],
            "cond2_ma150_above_ma200":     tpl["cond2_ma150_above_ma200"],
            "cond3_ma200_trending_up_1m":  tpl["cond3_ma200_trending_up_1m"],
            "cond4_ma50_above_150_200":    tpl["cond4_ma50_above_150_200"],
            "cond5_price_above_ma50":      tpl["cond5_price_above_ma50"],
            "cond6_30pct_above_52w_low":   tpl["cond6_30pct_above_52w_low"],
            "cond7_within_25pct_52w_high": tpl["cond7_within_25pct_52w_high"],
            "cond9_price_above_ema10":     tpl["cond9_price_above_ema10"],
            "fresh_ma12_cross_today":      tpl["fresh_ma12_cross_today"],
            "12m_return_pct": rs_ret,
            "volume_signal": vol_data["volume_signal"],
            "relative_volume": vol_data["relative_volume"],
            "bull_snort": vol_data["bull_snort"],
        }
    except Exception as exc:
        logger.error("Error processing %s: %r", sym, exc)
        return None


def download_all(symbols: list[str]) -> pd.DataFrame:
    """
    Download price history for all *symbols* in batches and return a
    consolidated DataFrame with indicators + trend-template flags.
    """
    all_rows: list[dict] = []
    total = ceil(len(symbols) / BATCH_SIZE)

    for i, batch in enumerate(_chunk(symbols, BATCH_SIZE), start=1):
        logger.info("=== Batch %d/%d (%d symbols) ===", i, total, len(batch))
        try:
            data = yf.download(
                tickers=batch,
                period=PERIOD,
                interval=INTERVAL,
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False,
            )
        except Exception as exc:
            logger.error("Batch %d download failed: %s", i, exc)
            continue

        if data is None or data.empty:
            continue

        is_multi = isinstance(data.columns, pd.MultiIndex)
        for sym in batch:
            row = _process_symbol(sym, data, is_multi)
            if row:
                all_rows.append(row)

    return pd.DataFrame(all_rows)
