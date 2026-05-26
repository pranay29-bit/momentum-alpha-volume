"""
scanner/main.py
---------------
Orchestrates the full scan pipeline:
  1. Load symbols from CSV
  2. Download & compute indicators in batches (yfinance)
  3. Apply Minervini trend-template + RS-percentile filters
  4. Enrich passing stocks with NSE market-cap data
  5. Write CSV outputs and HTML dashboards to docs/
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config     import DOCS_DIR
from .data_loader import download_all, load_symbols
from .nse_client  import enrich_with_market_caps
from .dashboard   import build_passing_dashboard, build_passing_ema10_dashboard, build_volume_action_dashboard, build_rocket_dashboard
from .result_calendar import get_result_date

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

COND_COLS = [
    "cond1_price_above_150_200",
    "cond2_ma150_above_ma200",
    "cond3_ma200_trending_up_1m",
    "cond4_ma50_above_150_200",
    "cond5_price_above_ma50",
    "cond6_30pct_above_52w_low",
    "cond7_within_25pct_52w_high",
    "cond8_rs_at_least_70",
]

def run() -> None:
    today_str    = datetime.today().strftime("%Y%m%d")
    date_display = datetime.today().strftime("%Y-%m-%d")

    # ── Output directory (GitHub Pages root + dated sub-folder) ──────────────
    out_dir = Path(DOCS_DIR) / date_display
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", out_dir)

    # ── 1. Symbols ────────────────────────────────────────────────────────────
    symbols = load_symbols()
    logger.info("Loaded %d symbols.", len(symbols))

    # ── 2. Download + indicators ──────────────────────────────────────────────
    df = download_all(symbols)
    if df.empty:
        logger.error("No valid data collected. Aborting.")
        sys.exit(1)
    logger.info("Collected rows for %d symbols.", len(df))

    # ── 3. RS percentile + condition flags ────────────────────────────────────
    df["rs_percentile"]        = df["12m_return_pct"].rank(pct=True) * 100.0
    df["cond8_rs_at_least_70"] = df["rs_percentile"] >= 70.0
    df["all_conditions_met"]   = df[COND_COLS].all(axis=1)

    # ── 4. Save full results ──────────────────────────────────────────────────
    full_path = out_dir / f"full_results_{today_str}.csv"
    df.to_csv(full_path, index=False)
    logger.info("Full results → %s", full_path)

    # ── 5. Passing stocks ─────────────────────────────────────────────────────
    passing = df[df["all_conditions_met"]].copy()

    if not passing.empty:
        passing = enrich_with_market_caps(passing)

    passing_path = out_dir / f"passing_stocks_{today_str}.csv"
    passing.to_csv(passing_path, index=False)
    logger.info("Passing stocks (%d) → %s", len(passing), passing_path)

    # ── 6. Passing + above EMA10 ──────────────────────────────────────────────
    if not passing.empty and "cond9_price_above_ema10" in passing.columns:
        passing_ema10 = (
            passing[passing["cond9_price_above_ema10"]]
            .sort_values("rs_percentile", ascending=False)
            .copy()
        )
    else:
        passing_ema10 = pd.DataFrame()

    ema10_path = out_dir / f"passing_ema10_{today_str}.csv"
    passing_ema10.to_csv(ema10_path, index=False)
    logger.info("Passing+EMA10 stocks (%d) → %s", len(passing_ema10), ema10_path)

    # ── 7. Fresh crossovers ───────────────────────────────────────────────────
    fresh      = df[df["fresh_ma12_cross_today"]].copy()
    fresh_path = out_dir / f"fresh_crossovers_{today_str}.csv"
    fresh.to_csv(fresh_path, index=False)
    logger.info("Fresh crossovers (%d) → %s", len(fresh), fresh_path)

    # ── 8. Volume Action ──────────────────────────────────────────────────────
    volume_action = df[df["volume_signal"] == "ppv"].copy()
    volume_action_path = out_dir / f"volume_action_{today_str}.csv"
    volume_action.to_csv(volume_action_path, index=False)

    # ── 8b. Rocket Stocks (passing + inside bar) ──────────────────────────────
    rocket = passing[passing["inside_bar"] == True].copy() 
    
    if "inside_bar" in passing.columns: 
      else pd.DataFrame()
    rocket_path = out_dir / f"rocket_stocks_{today_str}.csv"
    rocket.to_csv(rocket_path, index=False)
    logger.info("Rocket stocks (%d) → %s", len(rocket), rocket_path)

  

    # ── 9. HTML Dashboards ────────────────────────────────────────────────────
    if not passing.empty:
        build_passing_dashboard(
            passing,
            out_dir / f"dashboard_{today_str}.html",
            today_str,
        )
        # ── Rocket Stocks dashboard ──
        build_rocket_dashboard(
            passing,
            out_dir / f"rocket_dashboard_{today_str}.html",
            today_str,
        )
      
    if not passing_ema10.empty:
        # ── Collect historical elite-stock data from past dated folders ───────
        history: list[dict] = []
        docs_root = Path(DOCS_DIR)
        for dated_dir in sorted(docs_root.iterdir()):
            if not dated_dir.is_dir():
                continue
            dir_slug = dated_dir.name.replace("-", "")
            if not dir_slug.isdigit() or len(dir_slug) != 8:
                continue
            if dir_slug == today_str:
                continue  # today's point added by the dashboard builder
            csv_path = dated_dir / f"passing_ema10_{dir_slug}.csv"
            if not csv_path.exists():
                continue
            try:
                hist_df = pd.read_csv(csv_path)
                mc  = float(hist_df["total_market_cap_cr"].dropna().sum()) \
                      if "total_market_cap_cr" in hist_df.columns else 0.0
                tv  = float(hist_df["traded_value_cr"].dropna().sum()) \
                      if "traded_value_cr" in hist_df.columns else 0.0
                history.append({
                    "date":             dir_slug,
                    "count":            len(hist_df),
                    "market_cap_cr":    mc,
                    "traded_value_cr":  tv,
                })
            except Exception as exc:
                logger.warning("Could not read history from %s: %s", csv_path, exc)

        build_passing_ema10_dashboard(
            passing_ema10,
            out_dir / f"elite_dashboard_{today_str}.html",
            today_str,
            history=history,
        )

    if not volume_action.empty:
        build_volume_action_dashboard(
            volume_action,
            out_dir / f"volume_dashboard_{today_str}.html",
            today_str,
        )

    # ── 10. Update docs/index.html  (GitHub Pages landing page) ───────────────
    _update_index(today_str, out_dir, len(passing), len(passing_ema10))

    # ── 10. Console summary ───────────────────────────────────────────────────
    logger.info("── SUMMARY ──────────────────────────────")
    logger.info("  Total scanned   : %d", len(df))
    logger.info("  Passing (8 cond): %d", len(passing))
    logger.info("  Passing + EMA10 : %d", len(passing_ema10))
    logger.info("  Fresh crossovers: %d", len(fresh))
    logger.info("  Volume action   : %d", len(volume_action))

# ── Landing-page updater ──────────────────────────────────────────────────────

def _update_index(today_str: str, out_dir: Path, n_passing: int, n_elite: int) -> None:
    """Regenerate docs/index.html with a link to today's dashboards."""
    docs_root  = Path(DOCS_DIR)
    index_path = docs_root / "index.html"

    # Detect repo sub-path from environment (set by GitHub Actions)
    # e.g. GITHUB_REPOSITORY = "pranay29-bit/momentum-alpha-claude"
    repo        = os.environ.get("GITHUB_REPOSITORY", "")
    repo_name   = repo.split("/")[-1] if "/" in repo else ""
    base        = f"/{repo_name}" if repo_name else ""   # "" when using custom domain

    dated_dirs = sorted(
        [d for d in docs_root.iterdir() if d.is_dir() and d.name[:4].isdigit()],
        reverse=True,
    )

    rows = ""
    for d in dated_dirs:
        date_label = d.name
        try:
            date_label = datetime.strptime(d.name, "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            pass

        slug         = d.name.replace("-", "")
        passing_link = f"{d.name}/dashboard_{slug}.html"
        elite_link   = f"{base}/{d.name}/elite_dashboard_{slug}.html"

        rows += f"""
        <tr>
          <td class="date-cell">{date_label}</td>
          <td><a href="{passing_link}" class="btn-link">📊 Momentum Stocks</a></td>
          <td><a href="{elite_link}"   class="btn-link green">⚡ Elite Stocks</a></td>
          <td><a href="{d.name}/volume_dashboard_{slug}.html" class="btn-link">🔵 Volume Action</a></td>
          <td><a href="{d.name}/rocket_dashboard_{slug}.html" class="btn-link" style="background:#fff7ed;border-color:#fdba74;color:#c2410c">🚀 Rocket Stocks</a></td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Momentum Alpha — NSE Trend Scanner</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet"/>
<style>
  :root{{--bg:#f5f3ef;--surface:#fff;--border:#e4e0d8;--text:#1c1917;--muted:#78716c;
         --blue:#2563eb;--blue-bg:#eff6ff;--blue-mid:#bfdbfe;
         --emerald:#059669;--green-bg:#f0fdf4;--green-mid:#86efac;
         --sans:'Inter',sans-serif;--serif:'Playfair Display',Georgia,serif;}}
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:var(--sans);}}
  header{{background:var(--surface);border-bottom:1px solid var(--border);
          padding:2.5rem 3rem;text-align:center;}}
  .logo-dot{{display:inline-block;width:10px;height:10px;border-radius:50%;
             background:var(--emerald);margin-right:.4rem;vertical-align:middle;}}
  header h1{{font-family:var(--serif);font-size:2.4rem;font-weight:600;
             letter-spacing:-.02em;margin:.4rem 0;}}
  header p{{color:var(--muted);font-size:.9rem;}}
  .container{{max-width:860px;margin:3rem auto;padding:0 1.5rem;}}
  h2{{font-family:var(--serif);font-size:1.3rem;margin-bottom:1rem;}}
  table{{width:100%;border-collapse:collapse;background:var(--surface);
         border:1px solid var(--border);border-radius:14px;overflow:hidden;}}
  th{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;
      color:var(--muted);padding:.8rem 1.2rem;text-align:left;
      background:#faf9f7;border-bottom:1px solid var(--border);}}
  td{{padding:.9rem 1.2rem;border-bottom:1px solid var(--border);font-size:.88rem;}}
  tr:last-child td{{border-bottom:none;}}
  .date-cell{{font-weight:600;}}
  .btn-link{{display:inline-block;padding:.3rem .9rem;border-radius:999px;
             font-size:.78rem;font-weight:600;background:var(--blue-bg);
             border:1px solid var(--blue-mid);color:var(--blue);
             text-decoration:none;transition:background .15s;}}
  .btn-link:hover{{background:#dbeafe;}}
  .btn-link.green{{background:var(--green-bg);border-color:var(--green-mid);
                   color:var(--emerald);}}
  .btn-link.green:hover{{background:#dcfce7;}}
  footer{{text-align:center;padding:2rem;font-size:.72rem;color:var(--muted);
          border-top:1px solid var(--border);margin-top:3rem;}}
</style>
</head>
<body>
<header>
  <span class="logo-dot"></span>
  <span style="font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
               font-weight:700;color:var(--emerald)">Momentum Alpha</span>
  <h1>NSE Trend Scanner</h1>
  <p>Daily Minervini trend-template scans · Free-float &amp; liquidity data · NSE India</p>
</header>
<div class="container">
  <h2>Scan History</h2>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Minervini Trend Template Stocks</th>
        <th>Minervini Trend Template Stocks (Above EMA10)</th>
        <th>Volume Action Stocks</th>
        <th>Rocket Stocks</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<footer>
  Data sourced from NSE India &amp; Yahoo Finance &nbsp;·&nbsp;
  Updated daily at 18:00 IST &nbsp;·&nbsp;
  For informational purposes only — not financial advice
</footer>
</body>
</html>"""

    index_path.write_text(html, encoding="utf-8")
    logger.info("Index page updated → %s", index_path)

if __name__ == "__main__":
    run()
