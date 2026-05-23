"""
scanner/dashboard.py
--------------------
Generates self-contained HTML dashboards from scan results.

Three public entry-points:
  • build_passing_dashboard        – all 8-condition passing stocks
  • build_passing_ema10_dashboard  – passing AND above EMA10 (elite view)
  • build_index_page               – landing page with date navigation
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .utils import fmt_cr

logger = logging.getLogger(__name__)


# ── Small helpers ─────────────────────────────────────────────────────────────

def _safe(v) -> bool:
    try:
        return not np.isnan(float(v))
    except Exception:
        return False


def _r(v, n=2):
    try:
        f = float(v)
        return str(round(f, n)) if not np.isnan(f) else "null"
    except Exception:
        return "null"


def _tv_link(symbol_ns: str) -> str:
    sym = symbol_ns.replace(".NS", "").strip()
    return f"https://www.tradingview.com/chart/?symbol=NSE%3A{sym}"


# ── Shared CSS / Chart.js CDN ─────────────────────────────────────────────────

_CDN_CHARTJS = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
_GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700"
    "&family=Playfair+Display:wght@500;600&display=swap"
)

_BASE_CSS = """
:root {
  --bg:#f5f3ef; --surface:#ffffff; --border:#e4e0d8; --border2:#ccc8bf;
  --text:#1c1917; --muted:#78716c; --subtle:#a8a29e;
  --blue:#2563eb; --blue-bg:#eff6ff; --blue-mid:#bfdbfe;
  --teal:#0d9488; --amber:#b45309; --amber-bg:#fffbeb;
  --green:#15803d; --green-bg:#f0fdf4; --green-mid:#86efac;
  --emerald:#059669; --red:#dc2626;
  --purple:#7c3aed; --purple-bg:#f5f3ff;
  --sans:'Inter',sans-serif; --serif:'Playfair Display',Georgia,serif;
  --r:10px; --rl:14px;
}
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
html { font-size:15px; }
body { background:var(--bg); color:var(--text); font-family:var(--sans);
       line-height:1.6; min-height:100vh; }
a { color:inherit; text-decoration:none; }

/* ── Header ── */
header { background:var(--surface); border-bottom:1px solid var(--border);
         padding:1.75rem 3rem; display:flex; align-items:flex-end;
         justify-content:space-between; gap:1rem; flex-wrap:wrap; }
.logo-line { display:flex; align-items:center; gap:.6rem; margin-bottom:.3rem; }
.logo-dot  { width:8px; height:8px; border-radius:50%; }
.logo-tag  { font-size:.68rem; letter-spacing:.14em; text-transform:uppercase;
             font-weight:700; }
header h1  { font-family:var(--serif); font-size:clamp(1.5rem,3vw,2.1rem);
             font-weight:600; letter-spacing:-.02em; line-height:1.1; }
header .sub { font-size:.8rem; color:var(--muted); margin-top:.2rem; }
.date-chip  { border-radius:999px; padding:.35rem 1rem; font-size:.78rem;
              font-weight:700; white-space:nowrap; border:1px solid; }

/* ── KPI row ── */
.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
           gap:1rem; padding:1.5rem 3rem; }
.kpi { background:var(--surface); border:1px solid var(--border);
       border-radius:var(--rl); padding:1rem 1.3rem; position:relative;
       overflow:hidden; min-width:0; }
.kpi-accent { position:absolute; top:0; left:1.3rem; height:3px; width:28px;
              border-radius:0 0 3px 3px; }
.kpi-label  { font-size:.65rem; text-transform:uppercase; letter-spacing:.1em;
              color:var(--muted); font-weight:700; margin-bottom:.4rem; }
.kpi-val    { font-family:var(--serif); font-size:clamp(.95rem,2vw,1.65rem);
              font-weight:600; line-height:1; word-break:break-word; }
.kpi.blue   .kpi-val { color:var(--blue); }
.kpi.blue   .kpi-accent { background:var(--blue); }
.kpi.teal   .kpi-val { color:var(--teal); }
.kpi.teal   .kpi-accent { background:var(--teal); }
.kpi.amber  .kpi-val { color:var(--amber); }
.kpi.amber  .kpi-accent { background:var(--amber); }
.kpi.green  .kpi-val { color:var(--emerald); }
.kpi.green  .kpi-accent { background:var(--emerald); }
.kpi.purple .kpi-val { color:var(--purple); }
.kpi.purple .kpi-accent { background:var(--purple); }

/* ── Charts ── */
.charts-grid { padding:0 3rem 1.5rem; display:grid; gap:1rem;
               grid-template-columns:3fr 2fr; }
@media(max-width:860px) { .charts-grid { grid-template-columns:1fr; } }
.chart-card  { background:var(--surface); border:1px solid var(--border);
               border-radius:var(--rl); padding:1.25rem 1.4rem 1rem; }
.chart-title { font-size:.68rem; text-transform:uppercase; letter-spacing:.1em;
               color:var(--muted); font-weight:700; margin-bottom:1rem; }
.chart-wrap  { position:relative; height:250px; }

/* ── Table section ── */
.table-section { padding:0 3rem 3rem; }
.sec-head  { display:flex; align-items:center; justify-content:space-between;
             margin-bottom:.85rem; flex-wrap:wrap; gap:.75rem; }
.sec-title { font-size:.68rem; text-transform:uppercase; letter-spacing:.1em;
             color:var(--muted); font-weight:700; }
.controls  { display:flex; align-items:center; gap:1.25rem; flex-wrap:wrap; }
.search-input { background:var(--surface); border:1px solid var(--border2);
                border-radius:var(--r); color:var(--text); font-family:var(--sans);
                font-size:.82rem; padding:.4rem .85rem; outline:none; width:190px;
                transition:border-color .18s; }
.search-input::placeholder { color:var(--subtle); }
.legend { display:flex; gap:1.1rem; font-size:.7rem; color:var(--muted);
          flex-wrap:wrap; align-items:center; }
.leg-item { display:flex; align-items:center; gap:.3rem; }
.leg-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.tbl-wrap { background:var(--surface); border:1px solid var(--border);
            border-radius:var(--rl); overflow:auto; }
table { width:100%; border-collapse:collapse; font-size:.82rem; white-space:nowrap; }
thead tr { background:#faf9f7; border-bottom:1px solid var(--border);
           position:sticky; top:0; z-index:2; }
th { font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
     color:var(--muted); padding:.7rem 1rem; text-align:left; cursor:pointer;
     user-select:none; transition:background .12s; }
th:hover { background:#f0ede8; }
th.r { text-align:right; } th.c { text-align:center; }
th .si { margin-left:.3rem; opacity:.35; font-style:normal; font-size:.7rem; }
th.sort-asc  .si::after { content:'▲'; opacity:1; }
th.sort-desc .si::after { content:'▼'; opacity:1; }
th:not(.sort-asc):not(.sort-desc) .si::after { content:'⇅'; }
.srow { border-bottom:1px solid var(--border); transition:background .12s; }
.srow:last-child { border-bottom:none; }
.srow:hover { background:#fafaf8; }
td { padding:.7rem 1rem; vertical-align:middle; }
td.r { text-align:right; } td.c { text-align:center; }
a.sym-tag { display:inline-block; font-weight:700; font-size:.75rem;
            padding:.17rem .55rem; border-radius:6px; letter-spacing:.04em;
            text-decoration:none; border:1px solid; transition:background .15s; }
.rs-tag  { display:inline-block; background:var(--amber-bg); border:1px solid #fde68a;
           color:var(--amber); font-size:.73rem; font-weight:700;
           padding:.14rem .5rem; border-radius:999px; }
.ema-tag { display:inline-block; font-size:.73rem; font-weight:700;
           padding:.14rem .5rem; border-radius:999px; border:1px solid transparent; }
.bar-cell { display:flex; align-items:center; gap:.5rem; min-width:150px; }
.bar-bg   { flex:1; height:5px; background:#ebe9e4; border-radius:99px; overflow:hidden; }
.bar-fill { height:100%; border-radius:99px; }
.bar-pct  { font-size:.73rem; font-weight:700; min-width:36px; text-align:right; }
.badge    { font-size:.65rem; font-weight:700; letter-spacing:.06em;
            text-transform:uppercase; border-radius:999px; padding:.22rem .7rem;
            border:1px solid; }
.badge-row { display:flex; gap:.5rem; margin-top:.5rem; flex-wrap:wrap; }
footer { text-align:center; padding:1.1rem; font-size:.7rem; color:var(--subtle);
         border-top:1px solid var(--border); background:var(--surface); }
"""

_TABLE_SORT_JS = """
let sortCol = null, sortAsc = true;
document.querySelectorAll('#mainTable thead th').forEach(th => {
  th.addEventListener('click', () => {
    const col  = th.dataset.col;
    const type = th.dataset.type;
    if (!col) return;
    sortAsc = (sortCol === col) ? !sortAsc : true;
    sortCol = col;
    document.querySelectorAll('#mainTable thead th')
      .forEach(h => h.classList.remove('sort-asc','sort-desc'));
    th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
    const tbody = document.getElementById('tableBody');
    Array.from(tbody.querySelectorAll('.srow'))
      .sort((a, b) => {
        let av = a.dataset[col], bv = b.dataset[col];
        if (type === 'num') {
          av = parseFloat(av); bv = parseFloat(bv);
          if (isNaN(av)) av = -Infinity;
          if (isNaN(bv)) bv = -Infinity;
          return sortAsc ? av - bv : bv - av;
        }
        return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      })
      .forEach(r => tbody.appendChild(r));
  });
});
"""

_FILTER_JS = """
function filterRows() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  document.querySelectorAll('#tableBody .srow').forEach(r => {
    const sym    = (r.dataset.sym    || '').toLowerCase();
    const indgrp = (r.dataset.indgrp || '').toLowerCase();
    const ind    = (r.dataset.ind    || '').toLowerCase();
    r.style.display = (sym.includes(q) || indgrp.includes(q) || ind.includes(q)) ? '' : 'none';
  });
}
"""

_CHARTJS_DEFAULTS = """
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = "#78716c";
"""


def _html_head(title: str, accent: str = "var(--blue)") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<script src="{_CDN_CHARTJS}"></script>
<link href="{_GOOGLE_FONTS}" rel="stylesheet"/>
<style>{_BASE_CSS}</style>
</head>
<body>
"""


# ─────────────────────────────────────────────────────────────────────────────
#  PASSING STOCKS DASHBOARD  (all 8 Minervini conditions)
# ─────────────────────────────────────────────────────────────────────────────

def build_passing_dashboard(passing: pd.DataFrame, out_path: Path, date_str: str) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")

    n_stocks    = len(passing)
    n_above_ema = int(passing.get("cond9_price_above_ema10", pd.Series(dtype=bool)).sum()) \
                  if "cond9_price_above_ema10" in passing.columns else "N/A"
    total_tmc_s = fmt_cr(passing["total_market_cap_cr"].dropna().sum()) \
                  if "total_market_cap_cr" in passing.columns else "N/A"
    total_tv_s  = fmt_cr(passing["traded_value_cr"].dropna().sum()) \
                  if "traded_value_cr" in passing.columns else "N/A"

    rows_html = ""
    chart_labels, chart_total = [], []

    for _, row in passing.sort_values("rs_percentile", ascending=False).iterrows():
        sym        = str(row.get("symbol", "")).replace(".NS", "")
        link       = _tv_link(row.get("symbol", sym))
        close      = row.get("close", np.nan)
        ema10      = row.get("EMA10",  np.nan)
        rs         = row.get("rs_percentile", np.nan)
        tmc        = row.get("total_market_cap_cr", np.nan)
        tv         = row.get("traded_value_cr", np.nan)
        tvpct      = row.get("traded_val_pct_mc", np.nan)
        ind_grp    = str(row.get("industry_group", "")) or "—"
        industry   = str(row.get("industry", ""))       or "—"

        close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
        ema10_s = f"₹{float(ema10):,.2f}" if _safe(ema10) else "N/A"
        rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
        tmc_s   = fmt_cr(tmc)
        tv_s    = fmt_cr(tv)
        tvpct_s = f"{float(tvpct):.4f}%"  if _safe(tvpct) else "N/A"

        try:
            above_ema = float(close) > float(ema10)
            ema_col = "#15803d" if above_ema else "#dc2626"
            ema_bg  = "#dcfce7" if above_ema else "#fee2e2"
            ema_bdr = "#86efac" if above_ema else "#fca5a5"
        except Exception:
            ema_col = "#78716c"; ema_bg = "#f5f5f4"; ema_bdr = "#d4d0cb"

        rows_html += f"""
        <tr class="srow"
          data-sym="{sym}" data-close="{_r(close)}" data-rs="{_r(rs)}"
          data-ema10="{_r(ema10)}" data-tmc="{_r(tmc)}"
          data-tv="{_r(tv)}" data-tvpct="{_r(tvpct, 6)}"
          data-indgrp="{ind_grp}" data-ind="{industry}">
          <td><a class="sym-tag"
                 style="background:var(--blue-bg);border-color:#bfdbfe;color:#1d4ed8"
                 href="{link}" target="_blank" rel="noopener">{sym}</a></td>
          <td class="r">{close_s}</td>
          <td class="r"><span class="ema-tag"
               style="background:{ema_bg};border-color:{ema_bdr};color:{ema_col}">{ema10_s}</span></td>
          <td class="r"><span class="rs-tag">{rs_s}</span></td>
          <td class="r">{tmc_s}</td>
          <td class="r">{tv_s}</td>
          <td class="r">{tvpct_s}</td>
          <td>{ind_grp}</td>
          <td>{industry}</td>
        </tr>"""

        chart_labels.append(f'"{sym}"')
        chart_total.append(_r(tmc))

    html = _html_head(f"Market Cap Dashboard — {date_display}")
    html += f"""
<header>
  <div>
    <div class="logo-line">
      <div class="logo-dot" style="background:var(--blue)"></div>
      <span class="logo-tag" style="color:var(--blue)">Momentum Alpha · Minervini Scanner</span>
    </div>
    <h1>Market Cap Dashboard</h1>
    <p class="sub">Passing stocks · EMA10 filter · Market cap &amp; traded value · NSE data</p>
  </div>
  <div class="date-chip" style="background:var(--blue-bg);border-color:var(--blue-mid);color:var(--blue)">{date_display}</div>
</header>

<div class="kpi-row">
  <div class="kpi blue"><div class="kpi-accent"></div>
    <div class="kpi-label">Passing Stocks</div><div class="kpi-val">{n_stocks}</div></div>
  <div class="kpi purple"><div class="kpi-accent"></div>
    <div class="kpi-label">Above EMA10</div><div class="kpi-val">{n_above_ema}</div></div>
  <div class="kpi teal"><div class="kpi-accent"></div>
    <div class="kpi-label">Combined Market Cap</div><div class="kpi-val">{total_tmc_s}</div></div>
  <div class="kpi green"><div class="kpi-accent"></div>
    <div class="kpi-label">Total Traded Value</div><div class="kpi-val">{total_tv_s}</div></div>
</div>

<div class="charts-grid" style="grid-template-columns:1fr">
  <div class="chart-card">
    <div class="chart-title">Total Market Cap (₹ Cr)</div>
    <div class="chart-wrap"><canvas id="barChart"></canvas></div>
  </div>
</div>

<div class="table-section">
  <div class="sec-head">
    <span class="sec-title">Passing Stocks Detail</span>
    <div class="controls">
      <div class="legend">
        <div class="leg-item"><div class="leg-dot" style="background:#15803d"></div>Close &gt; EMA10</div>
        <div class="leg-item"><div class="leg-dot" style="background:#dc2626"></div>Close ≤ EMA10</div>
      </div>
      <input class="search-input" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-wrap">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"    data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close"  data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="ema10"  data-type="num">EMA10 ₹<i class="si"></i></th>
        <th class="r" data-col="rs"     data-type="num">RS %ile<i class="si"></i></th>
        <th class="r" data-col="result" data-type="str">Result Date<t class="si"></i></th>
        <th class="r" data-col="tmc"    data-type="num">Total Mkt Cap<i class="si"></i></th>
        <th class="r" data-col="tv"     data-type="num">Traded Value<i class="si"></i></th>
        <th class="r" data-col="tvpct"  data-type="num">TV % of Mkt Cap<i class="si"></i></th>
        <th          data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
        <th          data-col="ind"    data-type="str">Industry<i class="si"></i></th>
      </tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
</div>

<footer>Data from NSE India &nbsp;·&nbsp; Generated {date_display}
  &nbsp;·&nbsp; For informational purposes only &nbsp;·&nbsp; Not financial advice</footer>

<script>
const labels    = [{",".join(chart_labels)}];
const totalData = [{",".join(chart_total)}];
{_CHARTJS_DEFAULTS}
new Chart(document.getElementById('barChart'), {{
  type:'bar',
  data:{{ labels, datasets:[
    {{ label:'Total Mkt Cap', data:totalData, backgroundColor:'#bfdbfe',
       borderColor:'#93c5fd', borderWidth:1, borderRadius:4 }},
  ]}},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{
      legend:{{ labels:{{ boxWidth:10, boxHeight:10, padding:14 }} }},
      tooltip:{{ backgroundColor:'#fff', borderColor:'#e4e0d8', borderWidth:1,
        titleColor:'#1c1917', bodyColor:'#78716c', padding:10,
        callbacks:{{ label: c => ` ${{c.dataset.label}}: ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr` }} }},
    }},
    scales:{{
      x:{{ ticks:{{color:'#a8a29e'}}, grid:{{color:'#f0ede8'}} }},
      y:{{ ticks:{{color:'#a8a29e', callback: v=>'₹'+Number(v).toLocaleString('en-IN')}}, grid:{{color:'#f0ede8'}} }},
    }},
  }},
}});
{_FILTER_JS}
{_TABLE_SORT_JS}
</script>
</body></html>"""

    out_path.write_text(html, encoding="utf-8")
    logger.info("Passing dashboard → %s", out_path)


# ─────────────────────────────────────────────────────────────────────────────
#  ELITE DASHBOARD  (all 8 conditions + above EMA10)
# ─────────────────────────────────────────────────────────────────────────────

def build_passing_ema10_dashboard(
    df: pd.DataFrame,
    out_path: Path,
    date_str: str,
    history: list[dict] | None = None,
) -> None:
    """
    history: list of dicts with keys 'date' (YYYYMMDD str), 'count', 'market_cap_cr', 'traded_value_cr'
             sorted oldest → newest. If None/empty, charts show only today's single point.
    """
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")

    n_total     = len(df)
    total_tmc_s = fmt_cr(df["total_market_cap_cr"].dropna().sum()) \
                  if "total_market_cap_cr" in df.columns else "N/A"
    total_tv_s  = fmt_cr(df["traded_value_cr"].dropna().sum()) \
                  if "traded_value_cr" in df.columns else "N/A"

    rows_html = ""
    chart_labels, chart_total_mc = [], []

    for _, row in df.iterrows():
        sym      = str(row.get("symbol", "")).replace(".NS", "")
        link     = _tv_link(row.get("symbol", sym))
        close    = row.get("close",  np.nan)
        ema10    = row.get("EMA10",  np.nan)
        rs       = row.get("rs_percentile", np.nan)
        tmc      = row.get("total_market_cap_cr", np.nan)
        tv       = row.get("traded_value_cr", np.nan)
        tvpct    = row.get("traded_val_pct_mc", np.nan)
        ind_grp  = str(row.get("industry_group", "")) or "—"
        industry = str(row.get("industry", ""))       or "—"

        close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
        ema10_s = f"₹{float(ema10):,.2f}" if _safe(ema10) else "N/A"
        rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
        tmc_s   = fmt_cr(tmc)
        tv_s    = fmt_cr(tv)
        tvpct_s = f"{float(tvpct):.4f}%"  if _safe(tvpct) else "N/A"

        try:
            gap_pct = (float(close) - float(ema10)) / float(ema10) * 100
            gap_s   = f"+{gap_pct:.2f}%"
            gap_col = "#15803d"
        except Exception:
            gap_pct = -1.0; gap_s = "N/A"; gap_col = "#a8a29e"

        rows_html += f"""
        <tr class="srow"
          data-sym="{sym}" data-close="{_r(close)}" data-ema10="{_r(ema10)}"
          data-gap="{_r(gap_pct, 4)}" data-rs="{_r(rs)}" data-tmc="{_r(tmc)}"
          data-tv="{_r(tv)}" data-tvpct="{_r(tvpct, 6)}"
          data-indgrp="{ind_grp}" data-ind="{industry}">
          <td><a class="sym-tag"
                 style="background:var(--green-bg);border-color:var(--green-mid);color:var(--emerald)"
                 href="{link}" target="_blank" rel="noopener">{sym}</a></td>
          <td class="r">{close_s}</td>
          <td class="r"><span class="ema-tag"
               style="background:#f0fdf4;border-color:#86efac;color:var(--emerald)">{ema10_s}</span></td>
          <td class="r" style="color:{gap_col};font-weight:700">{gap_s}</td>
          <td class="r"><span class="rs-tag">{rs_s}</span></td>
          <td class="r">{tmc_s}</td>
          <td class="r">{tv_s}</td>
          <td class="r">{tvpct_s}</td>
          <td>{ind_grp}</td>
          <td>{industry}</td>
        </tr>"""

    # ── Build history line-chart data ─────────────────────────────────────────
    # history entries: {date: "YYYYMMDD", count: int, market_cap_cr: float, traded_value_cr: float}
    hist = list(history) if history else []

    # Ensure today's point is always present / up-to-date
    today_entry = {
        "date": date_str,
        "count": n_total,
        "market_cap_cr": float(df["total_market_cap_cr"].dropna().sum())
                         if "total_market_cap_cr" in df.columns else 0.0,
        "traded_value_cr": float(df["traded_value_cr"].dropna().sum())
                           if "traded_value_cr" in df.columns else 0.0,
    }
    # Replace or append today's entry
    hist = [h for h in hist if h.get("date") != date_str]
    hist.append(today_entry)
    hist.sort(key=lambda h: h["date"])

    def _fmt_date_label(d: str) -> str:
        try:
            return datetime.strptime(d, "%Y%m%d").strftime("%d %b")
        except Exception:
            return d

    hist_labels_js  = ",".join(f'"{_fmt_date_label(h["date"])}"' for h in hist)
    hist_count_js   = ",".join(str(int(h.get("count", 0)))         for h in hist)
    hist_mc_js      = ",".join(str(round(float(h.get("market_cap_cr", 0)), 2))     for h in hist)
    hist_tv_js      = ",".join(str(round(float(h.get("traded_value_cr", 0)), 2))   for h in hist)

    html = _html_head(f"Momentum Alpha — {date_display}")
    html += f"""
<header>
  <div>
    <div class="logo-line">
      <div class="logo-dot" style="background:var(--emerald)"></div>
      <span class="logo-tag" style="color:var(--emerald)">Momentum Alpha · Elite Filter</span>
    </div>
    <h1>Passing Stocks Above EMA10</h1>
    <p class="sub">All 8 Minervini conditions met &plus; Close &gt; 10-period EMA · NSE data</p>
    <div class="badge-row">
      <span class="badge" style="background:var(--green-bg);border-color:var(--green-mid);color:var(--emerald)">✓ All 8 Minervini Conditions</span>
      <span class="badge" style="background:var(--blue-bg);border-color:var(--blue-mid);color:var(--blue)">✓ Close &gt; EMA10</span>
    </div>
  </div>
  <div class="date-chip" style="background:var(--green-bg);border-color:var(--green-mid);color:var(--emerald)">{date_display}</div>
</header>

<div class="kpi-row">
  <div class="kpi green"><div class="kpi-accent"></div>
    <div class="kpi-label">Elite Stocks</div><div class="kpi-val">{n_total}</div></div>
  <div class="kpi teal"><div class="kpi-accent"></div>
    <div class="kpi-label">Combined Market Cap</div><div class="kpi-val">{total_tmc_s}</div></div>
  <div class="kpi blue"><div class="kpi-accent"></div>
    <div class="kpi-label">Total Traded Value</div><div class="kpi-val">{total_tv_s}</div></div>
</div>

<div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
  <div class="chart-card">
    <div class="chart-title">Elite Stock Count — Daily</div>
    <div class="chart-wrap"><canvas id="countChart"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">Combined Market Cap (₹ Cr) — Daily</div>
    <div class="chart-wrap"><canvas id="mcChart"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">Total Traded Value (₹ Cr) — Daily</div>
    <div class="chart-wrap"><canvas id="tvChart"></canvas></div>
  </div>
</div>

<div class="table-section">
  <div class="sec-head">
    <span class="sec-title">Elite Stocks Detail &nbsp;({n_total} stocks)</span>
    <div class="controls">
      <div class="legend">
        <div class="leg-item"><div class="leg-dot" style="background:#15803d"></div>FF ≥ 50%</div>
        <div class="leg-item"><div class="leg-dot" style="background:#b45309"></div>FF 25–50%</div>
        <div class="leg-item"><div class="leg-dot" style="background:#dc2626"></div>FF &lt; 25%</div>
      </div>
      <input class="search-input" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-wrap">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"    data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close"  data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="ema10"  data-type="num">EMA10 ₹<i class="si"></i></th>
        <th class="r" data-col="gap"    data-type="num">Gap % Above EMA10<i class="si"></i></th>
        <th class="r" data-col="rs"     data-type="num">RS %ile<i class="si"></i></th>
        <th class="r" data-col="result" data-type="str">Result Date<t class="si"></i></th>
        <th class="r" data-col="tmc"    data-type="num">Total Mkt Cap<i class="si"></i></th>
        <th class="r" data-col="tv"     data-type="num">Traded Value<i class="si"></i></th>
        <th class="r" data-col="tvpct"  data-type="num">TV % of Mkt Cap<i class="si"></i></th>
        <th          data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
        <th          data-col="ind"    data-type="str">Industry<i class="si"></i></th>
      </tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
</div>

<footer>Data from NSE India &nbsp;·&nbsp; Generated {date_display}
  &nbsp;·&nbsp; For informational purposes only &nbsp;·&nbsp; Not financial advice</footer>

<script>
const histLabels = [{hist_labels_js}];
const histCount  = [{hist_count_js}];
const histMC     = [{hist_mc_js}];
const histTV     = [{hist_tv_js}];
{_CHARTJS_DEFAULTS}

const _lineOpts = (yFmt, tooltipFmt) => ({{
  responsive: true, maintainAspectRatio: false,
  tension: 0.35,
  plugins: {{
    legend: {{ display: false }},
    tooltip: {{
      backgroundColor: '#fff', borderColor: '#e4e0d8', borderWidth: 1,
      titleColor: '#1c1917', bodyColor: '#78716c', padding: 10,
      callbacks: {{ label: tooltipFmt }},
    }},
  }},
  scales: {{
    x: {{ ticks: {{ color: '#a8a29e', maxTicksLimit: 10 }}, grid: {{ color: '#f0ede8' }} }},
    y: {{ ticks: {{ color: '#a8a29e', callback: yFmt }}, grid: {{ color: '#f0ede8' }} }},
  }},
}});

new Chart(document.getElementById('countChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [{{
    label: 'Elite Stocks', data: histCount,
    borderColor: '#059669', backgroundColor: 'rgba(5,150,105,0.08)',
    borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#059669', fill: true,
  }}]}},
  options: _lineOpts(
    v => v,
    c => ` Elite Stocks: ${{c.parsed.y}}`
  ),
}});

new Chart(document.getElementById('mcChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [{{
    label: 'Combined Mkt Cap', data: histMC,
    borderColor: '#0d9488', backgroundColor: 'rgba(13,148,136,0.08)',
    borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#0d9488', fill: true,
  }}]}},
  options: _lineOpts(
    v => '₹' + Number(v).toLocaleString('en-IN'),
    c => ` Mkt Cap: ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr`
  ),
}});

new Chart(document.getElementById('tvChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [{{
    label: 'Traded Value', data: histTV,
    borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.08)',
    borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#2563eb', fill: true,
  }}]}},
  options: _lineOpts(
    v => '₹' + Number(v).toLocaleString('en-IN'),
    c => ` Traded Value: ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr`
  ),
}});
{_FILTER_JS}
{_TABLE_SORT_JS}
</script>
</body></html>"""

    out_path.write_text(html, encoding="utf-8")
    logger.info("Elite dashboard → %s", out_path)


# ─────────────────────────────────────────────────────────────────────────────
#  VOLUME ACTION DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def build_volume_action_dashboard(volume_df: pd.DataFrame, out_path: Path, date_str: str) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")
    rows = ""
    for _, row in volume_df.sort_values("relative_volume", ascending=False).iterrows():
        sym = str(row.get("symbol", "")).replace(".NS", "")
        rows += f"""
        <tr class='srow'>
            <td><a class='sym-tag' href='{_tv_link(sym)}' target='_blank'>{sym}</a></td>
            <td class='r'>{round(float(row.get('close',0)),2)}</td>
            <td class='r'>{round(float(row.get('relative_volume',0)),1)}%</td>
            <td class='c'><span class='badge' style='background:var(--blue-bg);color:var(--blue);border-color:var(--blue-mid);'>BLUE PPV</span></td>
            <td class='c'>{'🔥' if row.get('bull_snort', False) else '-'}</td>
            <td class='r'><span class='rs-tag'>{round(float(row.get('rs_percentile',0)),1)}</span></td>
        </tr>
        """

    html = _html_head("Volume Action Dashboard") + f"""
    <header>
      <div><div class='logo-line'><span class='logo-dot' style='background:var(--blue)'></span><span class='logo-tag'>Momentum Alpha</span></div>
      <h1>Volume Action</h1><div class='sub'>Pocket Pivot / Blue Volume Stocks • {date_display}</div></div>
      <div class='date-chip' style='border-color:var(--blue-mid);background:var(--blue-bg);color:var(--blue);'>{len(volume_df)} Stocks</div>
    </header>
    <section class='table-section'>
    <div class='tbl-wrap'>
    <table>
    <thead><tr><th>Symbol</th><th class='r'>Close</th><th class='r'>Rel Volume</th><th class ='r'>Result Date</th><th class='c'>Signal</th><th class='c'>Bull Snort</th><th class='r'>RS</th></tr></thead>
    <tbody>{rows}</tbody></table></div></section></body></html>
    """
    out_path.write_text(html, encoding='utf-8')
    logger.info("Volume action dashboard → %s", out_path)
