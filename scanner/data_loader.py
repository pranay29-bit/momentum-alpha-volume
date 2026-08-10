"""
scanner/data_loader.py
----------------------
Loads symbol list from CSV and downloads OHLCV data from Yahoo Finance
in configurable batches. Also loads Industry & Industry Group metadata
from the same CSV and merges it into the result DataFrame.
"""

from __future__ import annotations

import logging
import time
from math import ceil
from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import (
    CSV_PATH, SYMBOL_COLUMN, EXCHANGE_SUFFIX,
    SME_CSV_PATH,
    PERIOD, INTERVAL, BATCH_SIZE, DOWNLOAD_THREADS,
)
from .indicators import add_indicators, evaluate_trend_template, compute_12m_return, compute_volume_action, is_inside_candle

logger = logging.getLogger(__name__)

# Seconds to pause between batches — prevents Yahoo Finance rate limiting.
# Batches now download concurrently (see DOWNLOAD_THREADS in config.py)
# instead of one symbol at a time, so a shorter inter-batch pause is enough.
_BATCH_DELAY        = 0.4
# Extra back-off when a 429 / rate-limit error is detected
_RATE_LIMIT_BACKOFF = 30.0


# ── Symbol list & metadata ─────────────────────────────────────────────────────

def _sme_code_to_yahoo(code: str) -> str | None:
    """
    Derive the Yahoo Finance ticker for one raw SME code.

    The SME CSV's "Symbols" column mixes both boards in a single field:
    - Purely numeric   → a BSE scrip code     → "<CODE>.BO"
    - Alphabetic       → an NSE trading code  → "<CODE>.NS"

    (Numeric codes sometimes round-trip through a spreadsheet as "542155.0"
    — that trailing ".0" is stripped before use.)
    """
    code = (code or "").strip()
    if not code or code.lower() == "nan":
        return None
    if code.endswith(".0") and code[:-2].isdigit():
        code = code[:-2]
    return f"{code}.BO" if code.isdigit() else f"{code}.NS"


def _sme_rows(csv_path: str = SME_CSV_PATH) -> pd.DataFrame:
    """
    Read the SME CSV and return it with a derived 'symbol_ns' column (the
    Yahoo ticker), handling both the current single-column schema
    (Name, Symbols, ISIN Code, Industry Group, Industry) and the older
    two-column schema (Name, BSE Code, NSE Code, ISIN Code, Industry Group,
    Industry) for backward compatibility.
    """
    df = pd.read_csv(csv_path, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    if "Symbols" in df.columns:
        df["symbol_ns"] = df["Symbols"].apply(_sme_code_to_yahoo)
    elif "NSE Code" in df.columns or "BSE Code" in df.columns:
        def _sym(row) -> str | None:
            nse_code = str(row.get("NSE Code", "") or "").strip()
            bse_code = str(row.get("BSE Code", "") or "").strip()
            if nse_code and nse_code.lower() != "nan":
                return _sme_code_to_yahoo(nse_code) or f"{nse_code}.NS"
            if bse_code and bse_code.lower() != "nan":
                return _sme_code_to_yahoo(bse_code) or f"{bse_code}.BO"
            return None
        df["symbol_ns"] = df.apply(_sym, axis=1)
    else:
        raise ValueError(
            f"{csv_path}: expected a 'Symbols' column (or legacy 'NSE Code'/"
            "'BSE Code' columns) — none found."
        )

    return df[df["symbol_ns"].notna()].copy()


def _sme_raw_codes(csv_path: str = SME_CSV_PATH) -> set[str]:
    """
    Raw, un-suffixed SME codes straight from the SME CSV (e.g. "AGUL",
    "542155") — used to filter SME rows out of the main-board universe by
    *code*, not by full Yahoo ticker. This matters because NSE_Stocks.csv
    turns out to already contain SME-board codes as plain rows (e.g. "AGUL"
    with no "-SM" marker) — those become "AGUL.NS" once the default ".NS"
    suffix is appended, which never equals the correct SME ticker
    "AGUL.NS", so a full-ticker comparison silently misses them.
    """
    try:
        df = pd.read_csv(csv_path, dtype=str)
    except Exception:
        return set()
    df.columns = [c.strip() for c in df.columns]

    codes: set[str] = set()
    cols = ["Symbols"] if "Symbols" in df.columns else ["NSE Code", "BSE Code"]
    for col in cols:
        if col in df.columns:
            vals = df[col].dropna().astype(str).str.strip()
            vals = vals[vals.str.lower() != "nan"]
            # Codes sometimes round-trip through spreadsheets as "542155.0"
            vals = vals.str.replace(r"\.0$", "", regex=True)
            codes.update(vals)
    return codes


def load_symbols(csv_path: str = CSV_PATH, symbol_col: str = SYMBOL_COLUMN) -> list[str]:
    df  = pd.read_csv(csv_path)
    raw = df[symbol_col].dropna().astype(str).str.strip().unique().tolist()

    # Safety net: drop any row whose *code* is actually an SME listing before
    # even building the Yahoo ticker, regardless of what NSE_Stocks.csv
    # contains. SME stocks are scanned/dashboarded separately (see
    # load_sme_symbols() below) — comparing raw codes (not full suffixed
    # tickers) is what actually catches SME rows that got exported into the
    # main-board CSV without their "-SM" marker.
    try:
        sme_codes = _sme_raw_codes(csv_path=SME_CSV_PATH)
    except Exception as exc:
        logger.debug("Could not load SME code set for exclusion check: %s", exc)
        sme_codes = set()
    if sme_codes:
        before = len(raw)
        raw = [s for s in raw if s not in sme_codes]
        removed = before - len(raw)
        if removed:
            logger.info("Excluded %d SME code(s) found in main-board CSV.", removed)

    symbols = [s if "." in s else s + EXCHANGE_SUFFIX for s in raw]

    # Belt-and-braces: also drop by full Yahoo ticker, in case a code was
    # already suffixed some other way in the main-board CSV.
    try:
        sme_set = set(load_sme_symbols())
    except Exception as exc:
        logger.debug("Could not load SME symbol set for exclusion check: %s", exc)
        sme_set = set()
    if sme_set:
        before = len(symbols)
        symbols = [s for s in symbols if s not in sme_set]
        removed = before - len(symbols)
        if removed:
            logger.info("Excluded %d SME symbol(s) (full-ticker match) from main-board universe.", removed)

    return symbols


def load_sme_symbols(csv_path: str = SME_CSV_PATH) -> list[str]:
    """
    Build the Yahoo Finance ticker list for the SME universe from the SME
    CSV (columns: Name, Symbols, ISIN Code, Industry Group, Industry — a
    numeric "Symbols" value is a BSE code, an alphabetic one is an NSE
    code; see _sme_code_to_yahoo()).

    - NSE-listed SME shares → "<CODE>.NS"
    - BSE-listed SME shares → "<CODE>.BO"
    """
    df = _sme_rows(csv_path)
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique = [s for s in df["symbol_ns"] if not (s in seen or seen.add(s))]
    return unique


def load_sme_metadata(csv_path: str = SME_CSV_PATH) -> pd.DataFrame:
    """
    Same shape as load_symbol_metadata(), but derived from the SME CSV and
    indexed by the SME Yahoo ticker (e.g. 'JALAN.NS' or '542155.BO').
    """
    df = _sme_rows(csv_path)

    meta_cols = {"symbol_ns": "symbol_ns"}
    if "Name" in df.columns:
        meta_cols["Name"] = "name"
    if "Industry Group" in df.columns:
        meta_cols["Industry Group"] = "industry_group"
    if "Industry" in df.columns:
        meta_cols["Industry"] = "industry"

    meta = df[[c for c in meta_cols]].rename(columns=meta_cols)
    return meta.drop_duplicates(subset=["symbol_ns"]).set_index("symbol_ns")


def load_symbol_metadata(csv_path: str = CSV_PATH, symbol_col: str = SYMBOL_COLUMN) -> pd.DataFrame:
    """
    Return a DataFrame indexed by the Yahoo-suffixed symbol with
    'industry_group' and 'industry' columns (sourced from NSE_Stocks.csv).
    """
    df = pd.read_csv(csv_path)
    df[symbol_col] = df[symbol_col].dropna().astype(str).str.strip()
    df = df[df[symbol_col].str.len() > 0].copy()

    # Same SME-code exclusion as load_symbols() — keeps this metadata table
    # in sync with the actual main-board universe it gets joined onto.
    try:
        sme_codes = _sme_raw_codes(csv_path=SME_CSV_PATH)
    except Exception:
        sme_codes = set()
    if sme_codes:
        df = df[~df[symbol_col].isin(sme_codes)]

    df["symbol_ns"] = df[symbol_col].apply(
        lambda s: s if "." in s else s + EXCHANGE_SUFFIX
    )

    meta_cols = {"symbol_ns": "symbol_ns"}
    if "Industry Group" in df.columns:
        meta_cols["Industry Group"] = "industry_group"
    if "Industry" in df.columns:
        meta_cols["Industry"] = "industry"

    meta = df[[c for c in meta_cols]].rename(columns=meta_cols)
    return meta.drop_duplicates(subset=["symbol_ns"]).set_index("symbol_ns")


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

        df_sym   = add_indicators(df_sym)
        tpl      = evaluate_trend_template(df_sym)
        rs_ret   = compute_12m_return(df_sym)
        vol_data = compute_volume_action(df_sym)
        inside_bar = is_inside_candle(df_sym)  

        # ── Close-based 52-week high/low flags (for Net New Highs breadth) ───
        # Standard market-breadth "new high/new low" counts use the closing
        # price reaching a new 52-week extreme, not the intraday High/Low.
        close_series   = df_sym["Close"]
        lookback       = min(252, len(close_series))
        close_roll_max = close_series.rolling(window=lookback, min_periods=1).max()
        close_roll_min = close_series.rolling(window=lookback, min_periods=1).min()
        is_52w_high_close = bool(close_series.iloc[-1] >= close_roll_max.iloc[-1])
        is_52w_low_close  = bool(close_series.iloc[-1] <= close_roll_min.iloc[-1])

        last_date = df_sym.index[-1]
        
        return {
            "symbol":  sym,
            "date": last_date.strftime("%Y-%m-%d"),
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
            "volume_signal":  vol_data["volume_signal"],
            "relative_volume": vol_data["relative_volume"],
            "bull_snort":     vol_data["bull_snort"],
            "inside_bar":     inside_bar,
            "is_52w_high":    is_52w_high_close,
            "is_52w_low":     is_52w_low_close,
        }
    except Exception as exc:
        logger.error("Error processing %s: %r", sym, exc)
        return None


def _retry_with_bse(failed_symbols: list[str], meta: pd.DataFrame) -> list[dict]:
    """
    Retry any symbols that failed to fetch on NSE (.NS) using the BSE (.BO)
    suffix instead. Some smaller/delisted-on-NSE tickers are still tradeable
    on BSE, so this recovers data that would otherwise be silently dropped.
    The output row's `symbol` field keeps the ORIGINAL .NS name (so industry
    metadata joins / dashboard links stay consistent) even though the price
    data underneath actually came from BSE.

    NSE-SME tickers ("<CODE>.NS") are skipped here: their BSE code is
    unrelated to the NSE code, so a naive ".NS" → ".BO" suffix swap would
    build a bogus ticker. SME stocks without an NSE listing are already
    downloaded directly as "<BSE CODE>.BO" by load_sme_symbols().
    """
    recovered: list[dict] = []
    bo_candidates = [s for s in failed_symbols if s.endswith(".NS") and "-.NS" not in s]
    if not bo_candidates:
        return recovered

    bo_map = {s: s[: -len(".NS")] + ".BO" for s in bo_candidates}
    bo_symbols = list(bo_map.values())

    logger.info("Retrying %d failed NSE symbols on BSE (.BO)…", len(bo_symbols))

    for i, batch in enumerate(_chunk(bo_symbols, BATCH_SIZE), start=1):
        if i > 1:
            time.sleep(_BATCH_DELAY)
        try:
            data = yf.download(
                tickers=batch, period=PERIOD, interval=INTERVAL,
                group_by="ticker", auto_adjust=True, threads=DOWNLOAD_THREADS, progress=False,
            )
        except Exception as exc:
            logger.warning("BSE fallback batch %d failed: %s", i, exc)
            continue
        if data is None or data.empty:
            continue

        is_multi = isinstance(data.columns, pd.MultiIndex)
        for bo_sym in batch:
            row = _process_symbol(bo_sym, data, is_multi)
            if row:
                original_ns = bo_sym[: -len(".BO")] + ".NS"
                row["symbol"] = original_ns  # keep NSE-style name for downstream joins/links
                row["data_source"] = "BSE"
                recovered.append(row)
                logger.info("Recovered %s via BSE (.BO) fallback.", original_ns)

    return recovered


def download_all(symbols: list[str], meta_override: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Download price history for all *symbols* in batches and return a
    consolidated DataFrame with indicators + trend-template flags,
    enriched with Industry Group and Industry from NSE_Stocks.csv.

    Any symbol that fails to fetch on NSE (.NS) is automatically retried
    on BSE (.BO) before being dropped — see _retry_with_bse().

    Pass `meta_override` (e.g. load_sme_metadata()) to enrich with a
    different metadata source than the default main-board CSV — used for
    the SME universe, which lives in its own CSV.
    """
    # Load industry metadata once
    if meta_override is not None:
        meta = meta_override
    else:
        try:
            meta = load_symbol_metadata()
        except Exception as exc:
            logger.warning("Could not load symbol metadata: %s", exc)
            meta = pd.DataFrame()

    all_rows: list[dict] = []
    failed_symbols: list[str] = []
    total = ceil(len(symbols) / BATCH_SIZE)

    for i, batch in enumerate(_chunk(symbols, BATCH_SIZE), start=1):
        # Polite pause between batches to avoid Yahoo Finance rate limiting
        if i > 1:
            time.sleep(_BATCH_DELAY)

        logger.info("=== Batch %d/%d (%d symbols) ===", i, total, len(batch))
        try:
            data = yf.download(
                tickers=batch,
                period=PERIOD,
                interval=INTERVAL,
                group_by="ticker",
                auto_adjust=True,
                threads=DOWNLOAD_THREADS,   # bounded concurrency within the batch
                progress=False,
            )
        except Exception as exc:
            err_str = str(exc).lower()
            if "too many requests" in err_str or "rate limit" in err_str or "429" in err_str:
                logger.warning(
                    "Rate limited on batch %d — backing off %ds then retrying once…",
                    i, _RATE_LIMIT_BACKOFF,
                )
                time.sleep(_RATE_LIMIT_BACKOFF)
                try:
                    data = yf.download(
                        tickers=batch,
                        period=PERIOD,
                        interval=INTERVAL,
                        group_by="ticker",
                        auto_adjust=True,
                        threads=DOWNLOAD_THREADS,
                        progress=False,
                    )
                except Exception as exc2:
                    logger.error("Batch %d retry also failed: %s", i, exc2)
                    failed_symbols.extend(batch)
                    continue
            else:
                logger.error("Batch %d download failed: %s", i, exc)
                failed_symbols.extend(batch)
                continue

        if data is None or data.empty:
            failed_symbols.extend(batch)
            continue

        is_multi = isinstance(data.columns, pd.MultiIndex)
        for sym in batch:
            row = _process_symbol(sym, data, is_multi)
            if row:
                all_rows.append(row)
            else:
                failed_symbols.append(sym)

    # ── BSE fallback for anything that failed on NSE ──────────────────────────
    if failed_symbols:
        recovered_rows = _retry_with_bse(failed_symbols, meta)
        all_rows.extend(recovered_rows)
        still_missing = len(failed_symbols) - len(recovered_rows)
        logger.info(
            "BSE fallback recovered %d/%d symbols (%d still unavailable).",
            len(recovered_rows), len(failed_symbols), still_missing,
        )

    df = pd.DataFrame(all_rows)

    # Merge industry metadata
    if not df.empty and not meta.empty:
        df = df.join(meta, on="symbol", how="left")

    return df
