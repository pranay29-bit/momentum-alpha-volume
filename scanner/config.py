"""
scanner/config.py
-----------------
All tuneable parameters for the Alpha Momentum scanner.
Override any value via environment variables before running.
"""

import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR     = ROOT_DIR / "data"
WEB_DIR      = ROOT_DIR / "web"
DOCS_DIR     = ROOT_DIR / "docs"          # GitHub Pages root

CSV_PATH     = os.getenv("NSE_CSV_PATH", str(DATA_DIR / "NSE_Stocks.csv"))
SYMBOL_COLUMN = "Symbol"
EXCHANGE_SUFFIX = ".NS"

# ── SME universe (separate board, separate dashboard) ────────────────────────
# NSE-listed SME shares trade on Yahoo as "<CODE>-SM.NS"; BSE-listed SME
# shares (no NSE listing) trade as "<CODE>.BO". Kept fully separate from the
# main-board CSV/pipeline above so SME stocks never appear in the Momentum
# or Elite dashboards — they only ever show up in the SME Momentum dashboard.
SME_CSV_PATH = os.getenv("SME_CSV_PATH", str(DATA_DIR / "SME_Stocks.csv"))

# ── Download ──────────────────────────────────────────────────────────────────
PERIOD    = "400d"
INTERVAL  = "1d"
BATCH_SIZE = 75
# yfinance's own intra-batch thread pool size. The old code passed
# threads=False (fully sequential — one symbol at a time over the network,
# ~3,000+ round trips for a full main+SME run), which was by far the
# slowest part of the whole pipeline. A small, fixed worker count keeps
# concurrency polite/bounded (unlike threads=True, which lets yfinance use
# an unbounded pool) while still being many times faster than serial.
DOWNLOAD_THREADS = int(os.getenv("DOWNLOAD_THREADS", "8"))

# ── Indicator windows ─────────────────────────────────────────────────────────
RS_LOOKBACK  = 252
MA12_WINDOW  = 12
MA36_WINDOW  = 36
MA50_WINDOW  = 50
MA150_WINDOW = 150
MA200_WINDOW = 200
EMA10_WINDOW = 10
EMA20_WINDOW = 20
CROSS_LOOKBACK = 10

# ── NSE API ───────────────────────────────────────────────────────────────────
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}
NSE_REQUEST_DELAY = 1.0   # seconds between per-stock NSE calls (per worker — see ENRICH_THREADS)
# Concurrency for the per-symbol market-cap/price-band enrichment step
# (nse_client.enrich_with_market_caps). This step was previously fully
# serial — one symbol at a time, each paying its own yfinance-retry +
# NSE_REQUEST_DELAY sleep — which made it the single biggest contributor
# to total run time after the price-history download itself. Each worker
# still paces its own calls the same as before; only the number of
# symbols in flight at once increases.
ENRICH_THREADS = int(os.getenv("ENRICH_THREADS", "6"))
