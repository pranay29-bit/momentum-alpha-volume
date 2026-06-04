
Claude finished the response
For this particular code I want the below things - 

https://github.com/pranay29-bit/momentum-alpha-volume

Make the font and everything else like the color format uniform across all the dashboards like description as well should be there in all the dashboards.
Jun 3
Let me start by reading the repository and the frontend design skill.


Fetched: GitHub - pranay29-bit/momentum-alpha-volume
Fetched: GitHub - pranay29-bit/momentum-alpha-volume
Now let me fetch the dashboard.py file which is the key file:


Searched the web
Searched the web
Let me fetch the files directly from the GitHub repo:


Searched the web, ran a command, viewed a file
Searched the web, ran a command, viewed a file
Claude's response was interrupted.
For this particular code I want the below things -
https://github.com/pranay29-bit/momentum-alpha-volume

Make the font and everything else like the color format uniform across all the dashboards like description as well should be there in all the dashboards.
Make another change the data should not come up for Saturday and Sunday as the markets are close on Saturday and Sunday so add a condition even if I run the workflow file it should create data for Saturday or Sunday.
Group the data month wise on the home page so that it would be easy for me to consolidate the data month wise.
Jun 3
Let me read all the relevant files first.


Viewed 4 files
Viewed 4 files
Now let me read the main.py and index.html:


Viewed 2 files
Viewed 2 files
Now let me read the workflow file:


Read the workflow file
Read the workflow file
Now I have a full picture. Let me implement all 3 changes:


Read the frontend skill
Read the frontend skill
Now I have everything I need. Let me implement all 3 changes:


Create working copy
Create working copy
Now let me make all the changes. Starting with Change 2 — weekend guard in main.py:


Add weekend guard at top of run() in main.py
Add weekend guard at top of run() in main.py
Now Change 1 — uniform font/colour/description across all dashboards. The Volume Action and Rocket dashboards are missing a description callout that the Passing and Elite dashboards have. Also the index page uses a different font stack (Inter/Playfair Display) vs the dashboards (Outfit/DM Mono). Let me unify everything:


Unify index page fonts/colors with dashboards, and add description callouts to Volume and Rocket dashboards
Unify index page fonts/colors with dashboards, and add description callouts to Volume and Rocket dashboards
Now Change 3 — group rows by month on the index page. Replace the rows building loop and the table HTML:


Replace flat rows loop with month-grouped HTML generation
Replace flat rows loop with month-grouped HTML generation
Now update the HTML template to use month_groups_html instead of the flat table:


Replace flat table with month-grouped rendering in HTML template
Replace flat table with month-grouped rendering in HTML template
Now add description callouts to the Volume Action dashboard (it was missing one), and to the Rocket dashboard. Also add a csv-bar to Volume Action for consistency. Let me update dashboard.py:


Add description callout and csv bar to Volume Action dashboard
Add description callout and csv bar to Volume Action dashboard
Now add a description callout to the Rocket dashboard (it already has one, let me check):


Check rocket dashboard callout
Check rocket dashboard callout
Good — Rocket already has a callout. Now let me add a callout to the Passing dashboard (which also lacks one) for full uniformity, and add one to the Elite dashboard:


Viewed a file, edited a file
Viewed a file, edited a file
Now add a callout to the Elite dashboard:


Viewed a file, edited a file
Viewed a file, edited a file
Now let me also add the .callout CSS to _BASE_CSS since Volume Action now uses it (it was only used by Rocket before; let me check it's already defined):


Check callout CSS definition
Check callout CSS definition
Good, .callout is in _BASE_CSS and shared across all dashboards. Now let me copy the files to the output:


Ran 5 commands
Ran 5 commands
All 3 changes are verified. Let me present the files:


Presented 3 files
Presented 3 files
Here's a summary of every change made across the two files:

1. dashboard.py — Uniform font, color, and descriptions
Fonts & colors unified on the index page (main.py): The landing page previously used Inter + Playfair Display with a warm-sepia palette (
#f5f3ef, 
#1c1917, 
#78716c) — completely different from the dashboards. It now uses the exact same Outfit + DM Mono fonts and the same CSS variables (--bg, --surface, --border, --indigo, --emerald, etc.) as all four dashboards.

Description callouts added to all 4 dashboards:

Dashboard	Had callout before?	Now
Passing Stocks	✗	✓ Explains 8 Minervini conditions
Elite Stocks	✗	✓ Explains EMA10 filter
Volume Action	✗	✓ Explains Pocket Pivot + Bull Snort
Rocket Stocks	✓ already	✓ unchanged
2. main.py — Weekend guard
Added at the very start of run(), before any output directory is created or data is downloaded:

python
weekday = today.weekday()  # Monday=0 … Sunday=6
if weekday >= 5:
    logger.warning("Today is Saturday/Sunday — NSE closed. Scan skipped.")
    sys.exit(0)
So even if you trigger workflow_dispatch manually on a Saturday, it exits cleanly with a log message and creates no folders, no CSVs, no HTML for that day.

3. main.py — Month-wise grouping on the home page
The flat <table> of all dates is replaced with grouped sections — one collapsible table per calendar month (e.g. June 2026, May 2026, etc.) using an OrderedDict keyed by "Month YYYY". The button links are also styled with the same accent colors as the dashboards they point to (indigo → Passing, green → Elite, blue → Volume, amber → Rocket).


Main
PY 

Dashboard
PY 

Daily scan
YML 
Change the font to what was before this font is not legible. And make the font and dashboard asthetic with white backgrond only

12:01 AM
Let me check what the original fonts looked like and the current state.


Ran 3 commands
Ran 3 commands
Good. Now I have the full picture:

Dashboards (dashboard.py): already use Outfit + DM Mono, white background (
#ffffff surface, 
#f7f8fc body) — these are fine
Index page (main.py): original used Inter + Playfair Display with a warm sepia tint (
#f5f3ef body) — needs to go back to Inter/Playfair but with a pure white background
The request is: revert the font to the original (Inter + Playfair Display on the index, Outfit + DM Mono on dashboards), and make everything white background. Let me apply that cleanly:


Ran a command, viewed a file
Ran a command, viewed a file
Now I have a clear picture. Let me rewrite the style block in main.py — restoring Inter + Playfair Display, full white background, and clean aesthetics — and also fix the --bg in dashboard.py to pure white:


Restore Inter/Playfair fonts, pure white background, refined aesthetics on index page
Restore Inter/Playfair fonts, pure white background, refined aesthetics on index page
Now fix dashboard.py — change --bg from the slightly-blue-tinted 
#f7f8fc to pure white, and --surface2/--surface3 to very clean white-adjacent tones:


Ran a command, edited a file
Ran a command, edited a file
Now update html { font-size } and body in _BASE_CSS — bump base font size to 15px so Outfit reads more comfortably:


Improve body font size and line-height for better legibility
Improve body font size and line-height for better legibility
Now update the header styles — the dashboard page headers should also feel crisper on white:


Update header background and table thead background to pure white/clean tones
Update header background and table thead background to pure white/clean tones
Now update the table font size for better readability (was .82rem, now .87rem):


Increase table font size for legibility
Increase table font size for legibility
Now copy both finished files to outputs:


Copy to outputs and verify
Copy to outputs and verify
There's a leftover old --bg:#f7f8fc in the build_main_index function (the standalone mini index builder). Let me fix that too:


Ran a command, viewed a file, edited a file
Ran a command, viewed a file, edited a file
Now fix the hardcoded old-palette colours in the chart JS (tooltip backgrounds, axis colours, grid lines):


Ran 2 commands
Ran 2 commands
Clean. Let me present both files:


Presented 2 files
Presented 2 files
Here's exactly what changed:

Index page (main.py)

Font restored to Inter (body) + Playfair Display (headings) — the original, highly legible pairing
Background changed from the sepia tint (
#f5f3ef) and the blue-tinted grey (
#f7f8fc) → pure 
#ffffff everywhere
Header, cards, footer, and sentiment cards all on white with clean 
#e8eaef borders
Dashboards (dashboard.py)

Outfit + DM Mono kept (these were always the dashboard fonts — no change there)
Base font size bumped from 14px → 15px so Outfit renders at a more comfortable reading size
Table row text bumped from .82rem → .87rem for better legibility
--bg changed from 
#f7f8fc → 
#ffffff (pure white page background)
--surface2 / --surface3 shifted to neutral warm-white (
#f8f9fb, 
#f1f3f7) rather than the blue-tinted greys
All hardcoded hex colours in chart tooltips, axis ticks, and grid lines updated to match the new white-background palette (
#6b7280, 
#9ca3af, 
#f8f9fb, 
#e8eaef)

Main
PY 

Dashboard
PY 
I am using the above given files only that looked more asthetically pleasing

12:12 AM
Got it — you want to go back to the version from the first response (the one before this last font change). Let me restore those exact files.


Restore the first response's files
Restore the first response's files
Claude's response was interrupted.
I have the response.

12:12 AM
The files from the first response are restored. Just drop main.py and dashboard.py into your scanner/ folder and you're good to go.


Presented 2 files
Presented 2 files
These are the exact files from the first response — Outfit + DM Mono fonts, the original colour palette, with all three changes (uniform descriptions, weekend guard, month grouping) intact.


Main
PY 

Dashboard
PY 
Please make these changes - 

FOr the month it should be coming in as a drop down with a smooth flow.
For graph that is there in the dashboard in that graph also remove Saturday and Sunday data. Also, the graph shouldnot be formed with Saturday and Sunday data.
12:14 AM
Let me read the current files carefully first.


Read current main.py month grouping section
Read current main.py month grouping section
Now let me read the Elite dashboard chart JS — that's where the history data feeds the graphs:


Viewed 2 files
Viewed 2 files
Now I have everything I need. Let me make both changes:


Working copies
Working copies
Change 1 — Month accordion dropdowns on index page:


Replace static month-group divs with animated accordion dropdowns
Replace static month-group divs with animated accordion dropdowns
Now replace the CSS and add accordion JS in the HTML template:


Replace month-group CSS with accordion styles and add JS
Replace month-group CSS with accordion styles and add JS
Now add the accordion JavaScript before </body>:


Add accordion JS before closing body tag
Add accordion JS before closing body tag
Change 2 — Strip weekends from Elite chart history in both main.py and dashboard.py:


Filter weekend dates out of history list before passing to elite dashboard
Filter weekend dates out of history list before passing to elite dashboard
Now in dashboard.py — the Elite dashboard builds hist from the history list passed in, then adds today's entry. Add a weekend filter there too so that even if any stale weekend data slipped into the list, it gets stripped before reaching the chart:


Strip weekends from hist list before building chart JS arrays
Strip weekends from hist list before building chart JS arrays
Now copy both to outputs:


Copy to outputs and verify all changes
Copy to outputs and verify all changes
All checks pass.


Presented 2 files
Presented 2 files
Here's exactly what was changed:

1. Month accordion dropdowns (main.py)

Each month section is now a clickable button that smoothly expands/collapses its table:

Open by default — all months start expanded so nothing is hidden on first load
Smooth CSS transition — uses max-height + opacity with cubic-bezier easing (0.38s), so the open/close feels fluid, not mechanical
Active state — the open button turns indigo-tinted to clearly signal which months are expanded
Chevron indicator — rotates 180° when collapsed so the state is always obvious
Scan count — shows e.g. "21 scans" next to the month name for quick reference
2. Weekend data stripped from Elite charts (both files)

main.py — when collecting historical Elite CSV data to build the chart series, any directory whose date falls on Saturday or Sunday is skipped before it's added to the history list
dashboard.py — after hist is assembled (including today's entry), a second _is_weekday() filter runs to catch any weekend entries that may have existed in older data, ensuring the chart arrays passed to Chart.js contain only weekday data points

Main
PY 

Dashboard
PY 






Claude is AI and can make mistakes. Please double-check responses.
Dashboard · PY
"""
scanner/dashboard.py
--------------------
Generates self-contained HTML dashboards from scan results.
 
Public entry-points:
  • build_passing_dashboard        – all 8-condition passing stocks
  • build_passing_ema10_dashboard  – passing AND above EMA10 (elite view)
  • build_volume_action_dashboard  – pocket pivot / volume action
  • build_rocket_dashboard         – passing + inside bar
  • build_main_index               – GitHub Pages landing page
 
New-stock tracking:
  Each dashboard accepts `known_symbols: set[str]` — symbols that appeared
  in ANY scan in the past 10 days. Symbols NOT in that set are marked ✦ NEW
  in the dashboard with a distinct highlight.
"""
 
from __future__ import annotations
 
import logging
from datetime import datetime
from pathlib import Path
 
import numpy as np
import pandas as pd
 
from .utils import fmt_cr
 
logger = logging.getLogger(__name__)
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
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
 
 
# ── Shared assets ─────────────────────────────────────────────────────────────
 
_CDN_CHARTJS  = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
_GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700"
    "&family=DM+Mono:wght@400;500&display=swap"
)
 
# ─── Design tokens ────────────────────────────────────────────────────────────
# Light-mode-first. Clean white with warm off-white accents.
# Accent palette: indigo (passing), emerald (elite), blue (volume), amber (rocket).
 
_BASE_CSS = """
:root {
  /* Surfaces */
  --bg:         #f7f8fc;
  --surface:    #ffffff;
  --surface2:   #f1f3f9;
  --surface3:   #e8ebf5;
  --border:     #e2e6f0;
  --border2:    #ccd1e4;
 
  /* Text */
  --text:       #0f1629;
  --muted:      #5a6282;
  --subtle:     #8b93b5;
 
  /* Brand accents */
  --indigo:     #4f46e5;
  --indigo-lt:  #eef0fd;
  --indigo-mid: #c7d2fe;
  --emerald:    #059669;
  --emerald-lt: #ecfdf5;
  --emerald-mid:#a7f3d0;
  --blue:       #2563eb;
  --blue-lt:    #eff6ff;
  --blue-mid:   #bfdbfe;
  --amber:      #d97706;
  --amber-lt:   #fffbeb;
  --amber-mid:  #fde68a;
  --red:        #dc2626;
  --red-lt:     #fef2f2;
  --violet:     #7c3aed;
  --violet-lt:  #f5f3ff;
  --violet-mid: #ddd6fe;
 
  /* NEW badge */
  --new-bg:     #fdf4ff;
  --new-border: #d946ef;
  --new-text:   #a21caf;
  --new-row:    #fdf4ff;
 
  /* Type */
  --sans:  'Outfit', system-ui, sans-serif;
  --mono:  'DM Mono', 'Courier New', monospace;
 
  /* Radii */
  --r:   8px;
  --rl:  12px;
  --rxl: 16px;
}
 
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  line-height: 1.6;
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }
 
/* ── Topbar ── */
.topbar {
  height: 3px;
  background: linear-gradient(90deg, var(--ACCENT1) 0%, var(--ACCENT2) 100%);
}
 
/* ── Header ── */
header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 1.6rem 2.5rem;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.hdr-left { display: flex; flex-direction: column; gap: .2rem; }
.brand {
  display: flex;
  align-items: center;
  gap: .5rem;
  margin-bottom: .25rem;
}
.brand-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
}
.brand-name {
  font-family: var(--mono);
  font-size: .65rem;
  font-weight: 500;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted);
}
header h1 {
  font-size: clamp(1.35rem, 2.5vw, 1.9rem);
  font-weight: 700;
  letter-spacing: -.03em;
  line-height: 1.1;
  color: var(--text);
}
.hdr-sub {
  font-size: .8rem;
  color: var(--muted);
  margin-top: .15rem;
}
.badge-row { display: flex; gap: .45rem; margin-top: .5rem; flex-wrap: wrap; }
.hdr-badge {
  font-size: .64rem;
  font-weight: 600;
  letter-spacing: .06em;
  text-transform: uppercase;
  border-radius: 999px;
  padding: .22rem .75rem;
  border: 1px solid;
}
.date-pill {
  font-family: var(--mono);
  font-size: .72rem;
  font-weight: 500;
  padding: .4rem 1.1rem;
  border-radius: 999px;
  border: 1px solid;
  white-space: nowrap;
  letter-spacing: .04em;
  align-self: flex-start;
  margin-top: .25rem;
}
 
/* ── CSV bar ── */
.csv-bar {
  display: flex;
  align-items: center;
  gap: .6rem;
  padding: .6rem 2.5rem;
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.csv-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: .35rem .95rem;
  font-family: var(--mono);
  font-size: .7rem;
  font-weight: 500;
  border-radius: var(--r);
  border: 1px solid;
  cursor: pointer;
  transition: background .14s;
  letter-spacing: .03em;
}
.csv-primary {
  background: var(--emerald-lt);
  border-color: var(--emerald-mid);
  color: var(--emerald);
}
.csv-primary:hover { background: #d1fae5; }
.csv-secondary {
  background: var(--blue-lt);
  border-color: var(--blue-mid);
  color: var(--blue);
}
.csv-secondary:hover { background: #dbeafe; }
.csv-label {
  font-family: var(--mono);
  font-size: .67rem;
  color: var(--subtle);
  margin-left: auto;
}
 
/* ── KPI strip ── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  border-bottom: 1px solid var(--border);
}
.kpi {
  background: var(--surface);
  padding: 1.1rem 1.6rem;
  border-right: 1px solid var(--border);
  position: relative;
}
.kpi:last-child { border-right: none; }
.kpi::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  border-radius: 0 0 2px 2px;
  background: var(--accent);
}
.kpi-lbl {
  font-size: .62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .11em;
  color: var(--muted);
  margin-bottom: .35rem;
}
.kpi-val {
  font-size: clamp(1.1rem, 2vw, 1.65rem);
  font-weight: 700;
  letter-spacing: -.02em;
  line-height: 1;
  color: var(--accent);
}
.kpi-hint {
  font-size: .67rem;
  color: var(--subtle);
  margin-top: .25rem;
}
 
/* ── Charts area ── */
.charts-area {
  padding: 1.1rem 2.5rem;
  display: grid;
  gap: .85rem;
}
.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--rl);
  padding: 1.1rem 1.3rem .9rem;
}
.chart-lbl {
  font-size: .62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .11em;
  color: var(--muted);
  margin-bottom: .8rem;
}
.chart-wrap { position: relative; height: 220px; }
 
/* ── Table section ── */
.table-sec { padding: 0 2.5rem 3rem; }
.tbl-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .9rem 0 .7rem;
  flex-wrap: wrap;
  gap: .6rem;
}
.tbl-title {
  font-size: .62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted);
}
.tbl-count { color: var(--ACCENT1); margin-left: .4rem; }
.controls { display: flex; align-items: center; gap: .85rem; flex-wrap: wrap; }
.search {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: var(--r);
  color: var(--text);
  font-family: var(--sans);
  font-size: .82rem;
  padding: .38rem .9rem;
  outline: none;
  width: 210px;
  transition: border-color .16s, box-shadow .16s;
}
.search::placeholder { color: var(--subtle); }
.search:focus {
  border-color: var(--ACCENT1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ACCENT1) 12%, transparent);
}
.legend-row { display: flex; gap: .9rem; align-items: center; flex-wrap: wrap; }
.leg { display: flex; align-items: center; gap: .3rem; font-size: .68rem; color: var(--muted); }
.leg-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
 
/* ── Table ── */
.tbl-outer {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--rl);
  overflow: hidden;
}
table { width: 100%; border-collapse: collapse; font-size: .82rem; white-space: nowrap; }
thead tr {
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 2;
}
th {
  font-size: .62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--muted);
  padding: .68rem 1rem;
  text-align: left;
  cursor: pointer;
  user-select: none;
  transition: background .12s;
  white-space: nowrap;
}
th:hover { background: var(--surface3); }
th.r { text-align: right; } th.c { text-align: center; }
th .si { margin-left: .25rem; opacity: .3; font-style: normal; font-size: .65rem; }
th.sort-asc  .si::after { content: '▲'; opacity: 1; color: var(--ACCENT1); }
th.sort-desc .si::after { content: '▼'; opacity: 1; color: var(--ACCENT1); }
th:not(.sort-asc):not(.sort-desc) .si::after { content: '⇅'; }
.srow { border-bottom: 1px solid var(--border); transition: background .1s; }
.srow:last-child { border-bottom: none; }
.srow:hover { background: var(--bg); }
td { padding: .65rem 1rem; vertical-align: middle; }
td.r { text-align: right; } td.c { text-align: center; }
 
/* ── NEW-stock highlight row ── */
.srow.is-new { background: var(--new-row); }
.srow.is-new:hover { background: #fae8ff; }
 
/* ── Symbol tags ── */
.sym-tag {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  font-family: var(--mono);
  font-weight: 500;
  font-size: .72rem;
  padding: .2rem .6rem;
  border-radius: 6px;
  letter-spacing: .05em;
  border: 1px solid;
  transition: filter .12s;
}
.sym-tag:hover { filter: brightness(.93); }
.sym-new-star {
  font-size: .55rem;
  background: var(--new-bg);
  border: 1px solid var(--new-border);
  color: var(--new-text);
  border-radius: 999px;
  padding: .1rem .38rem;
  font-weight: 700;
  letter-spacing: .04em;
  white-space: nowrap;
}
 
/* ── Value pills ── */
.pill {
  display: inline-block;
  font-family: var(--mono);
  font-size: .71rem;
  font-weight: 500;
  padding: .18rem .55rem;
  border-radius: 999px;
  border: 1px solid transparent;
}
.pill-green  { background: var(--emerald-lt); border-color: var(--emerald-mid); color: var(--emerald); }
.pill-red    { background: var(--red-lt);     border-color: #fca5a5;            color: var(--red); }
.pill-amber  { background: var(--amber-lt);   border-color: var(--amber-mid);   color: var(--amber); }
.pill-indigo { background: var(--indigo-lt);  border-color: var(--indigo-mid);  color: var(--indigo); }
.pill-blue   { background: var(--blue-lt);    border-color: var(--blue-mid);    color: var(--blue); }
.pill-muted  { background: var(--surface2);   border-color: var(--border2);     color: var(--muted); }
.pill-violet { background: var(--violet-lt);  border-color: var(--violet-mid);  color: var(--violet); }
 
/* ── Volume bar ── */
.vol-wrap { display: flex; align-items: center; gap: .5rem; min-width: 130px; }
.vol-bg   { flex: 1; height: 4px; background: var(--surface3); border-radius: 99px; overflow: hidden; }
.vol-fill { height: 100%; border-radius: 99px; }
.vol-pct  { font-family: var(--mono); font-size: .7rem; font-weight: 600; min-width: 42px; text-align: right; }
 
/* ── IB badge ── */
.ib-badge {
  display: inline-block;
  font-family: var(--mono);
  font-size: .58rem;
  font-weight: 600;
  background: var(--amber-lt);
  border: 1px solid var(--amber-mid);
  color: var(--amber);
  padding: .1rem .4rem;
  border-radius: 4px;
  margin-left: .3rem;
  letter-spacing: .04em;
  vertical-align: middle;
}
 
/* ── No-data row ── */
.no-data {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
  font-size: .82rem;
}
 
/* ── Info callout ── */
.callout {
  padding: .6rem 2.5rem;
  font-size: .78rem;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
 
/* ── Footer ── */
footer {
  text-align: center;
  padding: 1rem;
  font-size: .68rem;
  color: var(--subtle);
  border-top: 1px solid var(--border);
  background: var(--surface);
  font-family: var(--mono);
  letter-spacing: .04em;
}
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
    r.style.display = (sym.includes(q)||indgrp.includes(q)||ind.includes(q)) ? '' : 'none';
  });
}
"""
 
_CHARTJS_DEFAULTS = """
Chart.defaults.font.family = "'Outfit', sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = "#5a6282";
"""
 
 
def _html_head(title: str, accent1: str, accent2: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<script src="{_CDN_CHARTJS}"></script>
<link href="{_GOOGLE_FONTS}" rel="stylesheet"/>
<style>
:root {{ --ACCENT1:{accent1}; --ACCENT2:{accent2}; }}
{_BASE_CSS}
</style>
</head>
<body>
<div class="topbar"></div>
"""
 
 
def _new_star(is_new: bool) -> str:
    if not is_new:
        return ""
    return ' <span class="sym-new-star">✦ NEW</span>'
 
 
def _csv_bar_passing(date_str: str) -> str:
    sd = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    pf = f"passing_stocks_{date_str}.csv"
    ff = f"full_results_{date_str}.csv"
    return f"""
<div class="csv-bar">
  <a class="csv-btn csv-primary" href="{pf}" download="{pf}">⬇ Download Passing CSV</a>
  <a class="csv-btn csv-secondary" href="{ff}" download="{ff}">⬇ Full Results CSV</a>
  <span class="csv-label">Passing Stocks · Scan date: {sd}</span>
</div>"""
 
 
def _csv_bar_elite(date_str: str) -> str:
    sd = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    ef = f"passing_ema10_{date_str}.csv"
    return f"""
<div class="csv-bar">
  <a class="csv-btn csv-primary" href="{ef}" download="{ef}">⬇ Download Elite CSV</a>
  <span class="csv-label">Elite Stocks (Close &gt; EMA10) · Scan date: {sd}</span>
</div>"""
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  PASSING STOCKS DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
 
def build_passing_dashboard(
    passing: pd.DataFrame,
    out_path: Path,
    date_str: str,
    known_symbols: set[str] | None = None,
) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")
    known = known_symbols or set()
 
    n_stocks    = len(passing)
    n_above_ema = int(passing.get("cond9_price_above_ema10", pd.Series(dtype=bool)).sum()) \
                  if "cond9_price_above_ema10" in passing.columns else "N/A"
    total_tmc_s = fmt_cr(passing["total_market_cap_cr"].dropna().sum()) \
                  if "total_market_cap_cr" in passing.columns else "N/A"
    total_tv_s  = fmt_cr(passing["traded_value_cr"].dropna().sum()) \
                  if "traded_value_cr" in passing.columns else "N/A"
 
    rows_html = ""
    chart_labels, chart_total = [], []
 
    sort_col = "rs_percentile" if "rs_percentile" in passing.columns else "close"
    for _, row in passing.sort_values(sort_col, ascending=False).iterrows():
        sym        = str(row.get("symbol", "")).replace(".NS", "")
        link       = _tv_link(row.get("symbol", sym))
        is_new     = sym not in known
        new_cls    = " is-new" if is_new else ""
        close      = row.get("close", np.nan)
        ema10      = row.get("EMA10",  np.nan)
        rs         = row.get("rs_percentile", np.nan)
        tmc        = row.get("total_market_cap_cr", np.nan)
        tv         = row.get("traded_value_cr", np.nan)
        tvpct      = row.get("traded_val_pct_mc", np.nan)
        ind_grp    = str(row.get("industry_group", "")) or "—"
        industry   = str(row.get("industry",       "")) or "—"
        result_date = str(row.get("result_date", "—"))
        price_band  = str(row.get("price_band",  "—"))
 
        close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
        ema10_s = f"₹{float(ema10):,.2f}" if _safe(ema10) else "N/A"
        rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
        tmc_s   = fmt_cr(tmc)
        tv_s    = fmt_cr(tv)
        tvpct_s = f"{float(tvpct):.4f}%"  if _safe(tvpct) else "N/A"
 
        try:
            above_ema = float(close) > float(ema10)
            ema_cls = "pill-green" if above_ema else "pill-red"
        except Exception:
            ema_cls = "pill-muted"
 
        rows_html += f"""
        <tr class="srow{new_cls}"
          data-sym="{sym}" data-close="{_r(close)}" data-rs="{_r(rs)}"
          data-ema10="{_r(ema10)}" data-tmc="{_r(tmc)}"
          data-tv="{_r(tv)}" data-tvpct="{_r(tvpct,6)}"
          data-indgrp="{ind_grp}" data-ind="{industry}">
          <td>
            <a class="sym-tag" style="background:var(--indigo-lt);border-color:var(--indigo-mid);color:var(--indigo)"
               href="{link}" target="_blank" rel="noopener">{sym}{_new_star(is_new)}</a>
          </td>
          <td class="r" style="font-family:var(--mono)">{close_s}</td>
          <td class="r"><span class="pill {ema_cls}">{ema10_s}</span></td>
          <td class="r"><span class="pill pill-amber">{rs_s}</span></td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tmc_s}</td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tv_s}</td>
          <td class="r" style="font-family:var(--mono);color:var(--subtle);font-size:.73rem">{tvpct_s}</td>
          <td style="color:var(--muted);font-size:.78rem;max-width:150px;overflow:hidden;text-overflow:ellipsis">{ind_grp}</td>
          <td style="color:var(--subtle);font-size:.74rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">{industry}</td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{result_date}</td>
          <td class="c" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{price_band}</td>
        </tr>"""
 
        chart_labels.append(f'"{sym}"')
        chart_total.append(_r(tmc))
 
    n_new = sum(1 for _, r in passing.iterrows()
                if str(r.get("symbol","")).replace(".NS","") not in known)
 
    html  = _html_head(f"Momentum Alpha — Passing Stocks — {date_display}",
                       "var(--indigo)", "var(--blue)")
    html += _csv_bar_passing(date_str)
    html += f"""
<header>
  <div class="hdr-left">
    <div class="brand">
      <div class="brand-dot" style="background:var(--indigo)"></div>
      <span class="brand-name">Momentum Alpha · NSE Scanner</span>
    </div>
    <h1>Minervini Trend Template</h1>
    <p class="hdr-sub">All 8 Minervini conditions passing · NSE India · {date_display}</p>
    <div class="badge-row">
      <span class="hdr-badge" style="background:var(--indigo-lt);border-color:var(--indigo-mid);color:var(--indigo)">✓ All 8 Conditions</span>
      {"<span class='hdr-badge' style='background:var(--new-bg);border-color:var(--new-border);color:var(--new-text)'>✦ " + str(n_new) + " New Stocks</span>" if n_new else ""}
    </div>
  </div>
  <div class="date-pill" style="background:var(--indigo-lt);border-color:var(--indigo-mid);color:var(--indigo)">{date_display}</div>
</header>
 
<div class="kpi-strip" style="--accent:var(--indigo)">
  <div class="kpi" style="--accent:var(--indigo)">
    <div class="kpi-lbl">Passing Stocks</div>
    <div class="kpi-val">{n_stocks}</div>
    <div class="kpi-hint">all 8 conditions met</div>
  </div>
  <div class="kpi" style="--accent:var(--violet)">
    <div class="kpi-lbl">Above EMA10</div>
    <div class="kpi-val">{n_above_ema}</div>
    <div class="kpi-hint">close &gt; 10-period ema</div>
  </div>
  <div class="kpi" style="--accent:var(--emerald)">
    <div class="kpi-lbl">Combined Market Cap</div>
    <div class="kpi-val">{total_tmc_s}</div>
    <div class="kpi-hint">aggregate market cap</div>
  </div>
  <div class="kpi" style="--accent:var(--blue)">
    <div class="kpi-lbl">Total Traded Value</div>
    <div class="kpi-val">{total_tv_s}</div>
    <div class="kpi-hint">today's traded volume</div>
  </div>
  {"<div class='kpi' style='--accent:var(--new-text)'><div class='kpi-lbl'>New Appearances</div><div class='kpi-val'>" + str(n_new) + "</div><div class='kpi-hint'>first time in 10 days</div></div>" if n_new else ""}
</div>
 
<div class="callout">
  <strong style="color:var(--indigo)">Minervini Trend Template:</strong>
  Stocks satisfying all 8 conditions — price above MA150 &amp; MA200, MA150 &gt; MA200,
  MA200 trending up ≥ 1 month, MA50 above MA150 &amp; MA200, price above MA50,
  price ≥ 30% above 52-week low, within 25% of 52-week high, and RS percentile ≥ 70.
  These are momentum candidates in a confirmed Stage 2 uptrend.
</div>
 
<div class="charts-area" style="grid-template-columns:1fr">
  <div class="chart-card">
    <div class="chart-lbl">Total Market Cap by Stock (₹ Cr)</div>
    <div class="chart-wrap">
      <canvas id="barChart" role="img" aria-label="Market cap bar chart for passing stocks"></canvas>
    </div>
  </div>
</div>
 
<div class="table-sec">
  <div class="tbl-head">
    <div>
      <span class="tbl-title">Passing Stocks Detail</span>
      <span class="tbl-count tbl-title">[{n_stocks}]</span>
    </div>
    <div class="controls">
      <div class="legend-row">
        <div class="leg"><div class="leg-dot" style="background:var(--emerald)"></div>Close &gt; EMA10</div>
        <div class="leg"><div class="leg-dot" style="background:var(--red)"></div>Close ≤ EMA10</div>
        <div class="leg"><div class="leg-dot" style="background:var(--new-border)"></div>✦ New (10-day)</div>
      </div>
      <input class="search" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-outer">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"    data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close"  data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="ema10"  data-type="num">EMA10 ₹<i class="si"></i></th>
        <th class="r" data-col="rs"     data-type="num">RS %ile<i class="si"></i></th>
        <th class="r" data-col="tmc"    data-type="num">Mkt Cap<i class="si"></i></th>
        <th class="r" data-col="tv"     data-type="num">Traded Val<i class="si"></i></th>
        <th class="r" data-col="tvpct"  data-type="num">TV % MC<i class="si"></i></th>
        <th          data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
        <th          data-col="ind"    data-type="str">Industry<i class="si"></i></th>
        <th class="r">Result Date</th>
        <th class="c">Band</th>
      </tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
</div>
 
<footer>Data: NSE India &amp; Yahoo Finance · Generated {date_display} · For informational purposes only · Not financial advice</footer>
 
<script>
const labels    = [{",".join(chart_labels)}];
const totalData = [{",".join(chart_total)}];
{_CHARTJS_DEFAULTS}
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{ labels, datasets: [{{
    label: 'Mkt Cap (₹ Cr)', data: totalData,
    backgroundColor: 'rgba(79,70,229,0.12)',
    borderColor:     'rgba(79,70,229,0.45)',
    borderWidth: 1, borderRadius: 3,
  }}]}},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#fff', borderColor: '#e2e6f0', borderWidth: 1,
        titleColor: '#0f1629', bodyColor: '#5a6282', padding: 10,
        callbacks: {{ label: c => ` ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr` }},
      }},
    }},
    scales: {{
      x: {{ ticks: {{ color: '#8b93b5', maxTicksLimit: 30 }}, grid: {{ color: '#f1f3f9' }} }},
      y: {{ ticks: {{ color: '#8b93b5', callback: v => '₹' + Number(v).toLocaleString('en-IN') }},
            grid: {{ color: '#f1f3f9' }} }},
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
    known_symbols: set[str] | None = None,
) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")
    known = known_symbols or set()
 
    n_total     = len(df)
    total_tmc_s = fmt_cr(df["total_market_cap_cr"].dropna().sum()) \
                  if "total_market_cap_cr" in df.columns else "N/A"
    total_tv_s  = fmt_cr(df["traded_value_cr"].dropna().sum()) \
                  if "traded_value_cr" in df.columns else "N/A"
 
    rows_html = ""
    for _, row in df.iterrows():
        sym      = str(row.get("symbol", "")).replace(".NS", "")
        link     = _tv_link(row.get("symbol", sym))
        is_new   = sym not in known
        new_cls  = " is-new" if is_new else ""
        close    = row.get("close",  np.nan)
        ema10    = row.get("EMA10",  np.nan)
        rs       = row.get("rs_percentile", np.nan)
        tmc      = row.get("total_market_cap_cr", np.nan)
        tv       = row.get("traded_value_cr", np.nan)
        tvpct    = row.get("traded_val_pct_mc", np.nan)
        ind_grp  = str(row.get("industry_group", "")) or "—"
        industry = str(row.get("industry",       "")) or "—"
        result_date = str(row.get("result_date", "—"))
        price_band  = str(row.get("price_band",  "—"))
 
        close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
        ema10_s = f"₹{float(ema10):,.2f}" if _safe(ema10) else "N/A"
        rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
        tmc_s   = fmt_cr(tmc)
        tv_s    = fmt_cr(tv)
        tvpct_s = f"{float(tvpct):.4f}%"  if _safe(tvpct) else "N/A"
 
        try:
            gap_pct = (float(close) - float(ema10)) / float(ema10) * 100
            gap_s   = f"+{gap_pct:.2f}%"
            gap_col = "var(--emerald)"
        except Exception:
            gap_pct = -1.0; gap_s = "N/A"; gap_col = "var(--subtle)"
 
        rows_html += f"""
        <tr class="srow{new_cls}"
          data-sym="{sym}" data-close="{_r(close)}" data-ema10="{_r(ema10)}"
          data-gap="{_r(gap_pct,4)}" data-rs="{_r(rs)}" data-tmc="{_r(tmc)}"
          data-tv="{_r(tv)}" data-tvpct="{_r(tvpct,6)}"
          data-indgrp="{ind_grp}" data-ind="{industry}">
          <td>
            <a class="sym-tag" style="background:var(--emerald-lt);border-color:var(--emerald-mid);color:var(--emerald)"
               href="{link}" target="_blank" rel="noopener">{sym}{_new_star(is_new)}</a>
          </td>
          <td class="r" style="font-family:var(--mono)">{close_s}</td>
          <td class="r"><span class="pill pill-green">{ema10_s}</span></td>
          <td class="r" style="font-family:var(--mono);font-weight:600;color:{gap_col}">{gap_s}</td>
          <td class="r"><span class="pill pill-amber">{rs_s}</span></td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tmc_s}</td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tv_s}</td>
          <td class="r" style="font-family:var(--mono);color:var(--subtle);font-size:.73rem">{tvpct_s}</td>
          <td style="color:var(--muted);font-size:.78rem;max-width:150px;overflow:hidden;text-overflow:ellipsis">{ind_grp}</td>
          <td style="color:var(--subtle);font-size:.74rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">{industry}</td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{result_date}</td>
          <td class="c" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{price_band}</td>
        </tr>"""
 
    # History charts — filter out any weekend entries (NSE closed Sat/Sun)
    hist = list(history) if history else []
    today_entry = {
        "date": date_str, "count": n_total,
        "market_cap_cr":   float(df["total_market_cap_cr"].dropna().sum()) if "total_market_cap_cr" in df.columns else 0.0,
        "traded_value_cr": float(df["traded_value_cr"].dropna().sum())     if "traded_value_cr"     in df.columns else 0.0,
    }
    hist = [h for h in hist if h.get("date") != date_str]
    hist.append(today_entry)
    hist.sort(key=lambda h: h["date"])
    # Remove Saturday (weekday 5) and Sunday (weekday 6)
    def _is_weekday(d: str) -> bool:
        try:
            return datetime.strptime(d, "%Y%m%d").weekday() < 5
        except Exception:
            return True
    hist = [h for h in hist if _is_weekday(h.get("date", ""))]
 
    def _dl(d):
        try: return datetime.strptime(d, "%Y%m%d").strftime("%d %b")
        except: return d
 
    hl_js  = ",".join(f'"{_dl(h["date"])}"'                           for h in hist)
    hc_js  = ",".join(str(int(h.get("count", 0)))                     for h in hist)
    hmc_js = ",".join(str(round(float(h.get("market_cap_cr", 0)), 2)) for h in hist)
    htv_js = ",".join(str(round(float(h.get("traded_value_cr",0)),2)) for h in hist)
 
    n_new = sum(1 for _, r in df.iterrows()
                if str(r.get("symbol","")).replace(".NS","") not in known)
 
    html  = _html_head(f"Momentum Alpha — Elite Stocks — {date_display}",
                       "var(--emerald)", "var(--blue)")
    html += _csv_bar_elite(date_str)
    html += f"""
<header>
  <div class="hdr-left">
    <div class="brand">
      <div class="brand-dot" style="background:var(--emerald)"></div>
      <span class="brand-name">Momentum Alpha · Elite Filter</span>
    </div>
    <h1>Passing Stocks Above EMA10</h1>
    <p class="hdr-sub">All 8 Minervini conditions + Close &gt; 10-period EMA · NSE India · {date_display}</p>
    <div class="badge-row">
      <span class="hdr-badge" style="background:var(--emerald-lt);border-color:var(--emerald-mid);color:var(--emerald)">✓ 8 Minervini Conditions</span>
      <span class="hdr-badge" style="background:var(--blue-lt);border-color:var(--blue-mid);color:var(--blue)">✓ Close &gt; EMA10</span>
      {"<span class='hdr-badge' style='background:var(--new-bg);border-color:var(--new-border);color:var(--new-text)'>✦ " + str(n_new) + " New Stocks</span>" if n_new else ""}
    </div>
  </div>
  <div class="date-pill" style="background:var(--emerald-lt);border-color:var(--emerald-mid);color:var(--emerald)">{date_display}</div>
</header>
 
<div class="kpi-strip">
  <div class="kpi" style="--accent:var(--emerald)">
    <div class="kpi-lbl">Elite Stocks</div>
    <div class="kpi-val">{n_total}</div>
    <div class="kpi-hint">all filters passing</div>
  </div>
  <div class="kpi" style="--accent:var(--blue)">
    <div class="kpi-lbl">Combined Market Cap</div>
    <div class="kpi-val">{total_tmc_s}</div>
    <div class="kpi-hint">aggregate market cap</div>
  </div>
  <div class="kpi" style="--accent:var(--indigo)">
    <div class="kpi-lbl">Total Traded Value</div>
    <div class="kpi-val">{total_tv_s}</div>
    <div class="kpi-hint">today's traded volume</div>
  </div>
  {"<div class='kpi' style='--accent:var(--new-text)'><div class='kpi-lbl'>New Appearances</div><div class='kpi-val'>" + str(n_new) + "</div><div class='kpi-hint'>first time in 10 days</div></div>" if n_new else ""}
</div>
 
<div class="callout">
  <strong style="color:var(--emerald)">Elite Filter:</strong>
  All 8 Minervini conditions met <strong>AND</strong> the latest close is above the 10-period EMA —
  indicating the stock is in an active, accelerating uptrend. These are the highest-conviction
  actionable buy candidates from today's scan.
</div>
 
<div class="charts-area" style="grid-template-columns:1fr 1fr 1fr">
  <div class="chart-card">
    <div class="chart-lbl">Elite Stock Count — Daily</div>
    <div class="chart-wrap"><canvas id="countChart" role="img" aria-label="Elite stock count over time"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-lbl">Combined Market Cap (₹ Cr) — Daily</div>
    <div class="chart-wrap"><canvas id="mcChart" role="img" aria-label="Combined market cap over time"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-lbl">Total Traded Value (₹ Cr) — Daily</div>
    <div class="chart-wrap"><canvas id="tvChart" role="img" aria-label="Total traded value over time"></canvas></div>
  </div>
</div>
 
<div class="table-sec">
  <div class="tbl-head">
    <div>
      <span class="tbl-title">Elite Stocks Detail</span>
      <span class="tbl-count tbl-title">[{n_total}]</span>
    </div>
    <div class="controls">
      <div class="legend-row">
        <div class="leg"><div class="leg-dot" style="background:var(--new-border)"></div>✦ New (10-day)</div>
      </div>
      <input class="search" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-outer">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"   data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close"  data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="ema10"  data-type="num">EMA10 ₹<i class="si"></i></th>
        <th class="r" data-col="gap"    data-type="num">Gap % Above EMA10<i class="si"></i></th>
        <th class="r" data-col="rs"     data-type="num">RS %ile<i class="si"></i></th>
        <th class="r" data-col="tmc"    data-type="num">Mkt Cap<i class="si"></i></th>
        <th class="r" data-col="tv"     data-type="num">Traded Val<i class="si"></i></th>
        <th class="r" data-col="tvpct"  data-type="num">TV % MC<i class="si"></i></th>
        <th          data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
        <th          data-col="ind"    data-type="str">Industry<i class="si"></i></th>
        <th class="r">Result Date</th>
        <th class="c">Band</th>
      </tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
</div>
 
<footer>Data: NSE India &amp; Yahoo Finance · Generated {date_display} · For informational purposes only · Not financial advice</footer>
 
<script>
const histLabels = [{hl_js}];
const histCount  = [{hc_js}];
const histMC     = [{hmc_js}];
const histTV     = [{htv_js}];
{_CHARTJS_DEFAULTS}
const lineDs = (data, color) => ({{
  data,
  borderColor: color,
  backgroundColor: color.replace('rgb','rgba').replace(')',',0.07)'),
  borderWidth: 2, pointRadius: 3.5, pointBackgroundColor: color, fill: true, tension: 0.35,
}});
const lineOpts = (yFmt, tipFmt) => ({{
  responsive: true, maintainAspectRatio: false,
  plugins: {{
    legend: {{ display: false }},
    tooltip: {{
      backgroundColor: '#fff', borderColor: '#e2e6f0', borderWidth: 1,
      titleColor: '#0f1629', bodyColor: '#5a6282', padding: 10,
      callbacks: {{ label: tipFmt }},
    }},
  }},
  scales: {{
    x: {{ ticks: {{ color: '#8b93b5', maxTicksLimit: 10 }}, grid: {{ color: '#f1f3f9' }} }},
    y: {{ ticks: {{ color: '#8b93b5', callback: yFmt }}, grid: {{ color: '#f1f3f9' }} }},
  }},
}});
new Chart(document.getElementById('countChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [lineDs(histCount, 'rgb(5,150,105)')] }},
  options: lineOpts(v => v, c => ` ${{c.parsed.y}} stocks`),
}});
new Chart(document.getElementById('mcChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [lineDs(histMC, 'rgb(37,99,235)')] }},
  options: lineOpts(v => '₹'+Number(v).toLocaleString('en-IN'), c => ` ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr`),
}});
new Chart(document.getElementById('tvChart'), {{
  type: 'line',
  data: {{ labels: histLabels, datasets: [lineDs(histTV, 'rgb(79,70,229)')] }},
  options: lineOpts(v => '₹'+Number(v).toLocaleString('en-IN'), c => ` ₹${{(c.parsed.y||0).toLocaleString('en-IN')}} Cr`),
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
 
def build_volume_action_dashboard(
    volume_df: pd.DataFrame,
    out_path: Path,
    date_str: str,
    known_symbols: set[str] | None = None,
) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")
    known = known_symbols or set()
    rows = ""
 
    for _, row in volume_df.sort_values("relative_volume", ascending=False).iterrows():
        sym        = str(row.get("symbol", "")).replace(".NS", "")
        is_new     = sym not in known
        new_cls    = " is-new" if is_new else ""
        close      = row.get("close", np.nan)
        rel_vol    = row.get("relative_volume", np.nan)
        rs         = row.get("rs_percentile", np.nan)
        ind_grp    = str(row.get("industry_group", "")) or "—"
        industry   = str(row.get("industry",       "")) or "—"
        result_date = str(row.get("result_date", "—"))
        price_band  = str(row.get("price_band",  "—"))
        bull_snort  = row.get("bull_snort", False)
 
        close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
        rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
 
        try:
            rv = float(rel_vol)
            bar_pct = min(rv / 500 * 100, 100)
            rv_s = f"{rv:.1f}%"
            if rv > 200:   bar_col = "var(--red)"
            elif rv > 100: bar_col = "var(--amber)"
            else:          bar_col = "var(--emerald)"
        except Exception:
            bar_pct = 0; rv_s = "N/A"; bar_col = "var(--muted)"
 
        snort_cell = ('<span class="pill pill-amber" style="font-size:.65rem">🔥 SNORT</span>'
                      if bull_snort else
                      '<span style="color:var(--subtle);font-size:.74rem">—</span>')
 
        rows += f"""
        <tr class="srow{new_cls}"
          data-sym="{sym}" data-indgrp="{ind_grp}" data-ind="{industry}"
          data-close="{_r(close)}" data-relvol="{_r(rel_vol)}" data-rs="{_r(rs)}">
          <td>
            <a class="sym-tag" style="background:var(--blue-lt);border-color:var(--blue-mid);color:var(--blue)"
               href="{_tv_link(sym)}" target="_blank" rel="noopener">{sym}{_new_star(is_new)}</a>
          </td>
          <td class="r" style="font-family:var(--mono)">{close_s}</td>
          <td class="r">
            <div class="vol-wrap">
              <div class="vol-bg"><div class="vol-fill" style="width:{bar_pct:.1f}%;background:{bar_col}"></div></div>
              <span class="vol-pct" style="color:{bar_col}">{rv_s}</span>
            </div>
          </td>
          <td class="c"><span class="pill pill-blue" style="font-size:.65rem;letter-spacing:.04em">BLUE PPV</span></td>
          <td class="c">{snort_cell}</td>
          <td class="r"><span class="pill pill-amber">{rs_s}</span></td>
          <td style="color:var(--muted);font-size:.78rem">{ind_grp}</td>
          <td style="color:var(--subtle);font-size:.74rem">{industry}</td>
          <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{result_date}</td>
          <td class="c" style="font-family:var(--mono);color:var(--muted);font-size:.74rem">{price_band}</td>
        </tr>"""
 
    n_new = sum(1 for _, r in volume_df.iterrows()
                if str(r.get("symbol","")).replace(".NS","") not in known)
 
    html  = _html_head(f"Momentum Alpha — Volume Action — {date_display}",
                       "var(--blue)", "var(--indigo)")
    html += f"""
<header>
  <div class="hdr-left">
    <div class="brand">
      <div class="brand-dot" style="background:var(--blue)"></div>
      <span class="brand-name">Momentum Alpha · Volume Action</span>
    </div>
    <h1>Pocket Pivot Stocks</h1>
    <p class="hdr-sub">Blue volume / pocket pivot events · NSE India · {date_display}</p>
    <div class="badge-row">
      <span class="hdr-badge" style="background:var(--blue-lt);border-color:var(--blue-mid);color:var(--blue)">✓ Pocket Pivot Volume</span>
      {"<span class='hdr-badge' style='background:var(--new-bg);border-color:var(--new-border);color:var(--new-text)'>✦ " + str(n_new) + " New Stocks</span>" if n_new else ""}
    </div>
  </div>
  <div class="date-pill" style="background:var(--blue-lt);border-color:var(--blue-mid);color:var(--blue)">{len(volume_df)} Stocks · {date_display}</div>
</header>
 
<div class="kpi-strip">
  <div class="kpi" style="--accent:var(--blue)">
    <div class="kpi-lbl">PPV Stocks</div>
    <div class="kpi-val">{len(volume_df)}</div>
    <div class="kpi-hint">pocket pivot volume</div>
  </div>
  {"<div class='kpi' style='--accent:var(--new-text)'><div class='kpi-lbl'>New Appearances</div><div class='kpi-val'>" + str(n_new) + "</div><div class='kpi-hint'>first time in 10 days</div></div>" if n_new else ""}
</div>
 
<div class="callout">
  <strong style="color:var(--blue)">Pocket Pivot Volume (PPV):</strong>
  Today's volume exceeds the highest <em>down-day</em> volume of the prior 10 sessions while the stock closes in the upper portion of its range —
  a sign of institutional accumulation in a trending stock.
  <strong>Bull Snort</strong> signals unusually explosive volume (&gt; 200% relative) alongside a bullish close.
</div>
 
<div class="table-sec" style="padding-top:1.1rem">
  <div class="tbl-head">
    <div>
      <span class="tbl-title">Volume Action Stocks</span>
      <span class="tbl-count tbl-title">[{len(volume_df)}]</span>
    </div>
    <div class="controls">
      <div class="legend-row">
        <div class="leg"><div class="leg-dot" style="background:var(--new-border)"></div>✦ New (10-day)</div>
      </div>
      <input class="search" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-outer">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"    data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close"  data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="relvol" data-type="num">Rel Volume<i class="si"></i></th>
        <th class="c">Signal</th>
        <th class="c">Bull Snort</th>
        <th class="r" data-col="rs"    data-type="num">RS %ile<i class="si"></i></th>
        <th data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
        <th data-col="ind"    data-type="str">Industry<i class="si"></i></th>
        <th class="r">Result Date</th>
        <th class="c">Band</th>
      </tr></thead>
      <tbody id="tableBody">{rows}</tbody>
    </table>
  </div>
</div>
 
<footer>Data: NSE India &amp; Yahoo Finance · Generated {date_display} · For informational purposes only · Not financial advice</footer>
 
<script>
{_FILTER_JS}
{_TABLE_SORT_JS}
</script>
</body></html>"""
 
    out_path.write_text(html, encoding="utf-8")
    logger.info("Volume action dashboard → %s", out_path)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  ROCKET DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
 
def build_rocket_dashboard(
    passing: pd.DataFrame,
    out_path: Path,
    date_str: str,
    known_symbols: set[str] | None = None,
) -> None:
    date_display = datetime.strptime(date_str, "%Y%m%d").strftime("%d %b %Y")
    known = known_symbols or set()
 
    rocket    = passing[passing["inside_bar"] == True].copy() \
                if "inside_bar" in passing.columns else pd.DataFrame()
    n_rocket  = len(rocket)
    n_passing = len(passing)
 
    if n_rocket == 0:
        rows_html = f'<tr><td colspan="9" class="no-data">No Rocket Stocks today — no inside bars among {n_passing} passing stocks.</td></tr>'
    else:
        rows_html = ""
        for _, row in rocket.sort_values("rs_percentile", ascending=False).iterrows():
            sym      = str(row.get("symbol", "")).replace(".NS", "")
            link     = _tv_link(row.get("symbol", sym))
            is_new   = sym not in known
            new_cls  = " is-new" if is_new else ""
            close    = row.get("close",  np.nan)
            ema10    = row.get("EMA10",  np.nan)
            rs       = row.get("rs_percentile", np.nan)
            tmc      = row.get("total_market_cap_cr", np.nan)
            tv       = row.get("traded_value_cr", np.nan)
            hi52_pct = row.get("pct_from_52w_high", np.nan)
            lo52_pct = row.get("pct_above_52w_low", np.nan)
            ind_grp  = str(row.get("industry_group", "")) or "—"
 
            close_s = f"₹{float(close):,.2f}" if _safe(close) else "N/A"
            ema10_s = f"₹{float(ema10):,.2f}" if _safe(ema10) else "N/A"
            rs_s    = f"{float(rs):.1f}"       if _safe(rs)    else "N/A"
            tmc_s   = fmt_cr(tmc)
            tv_s    = fmt_cr(tv)
 
            if not _safe(hi52_pct) and _safe(close) and _safe(row.get("52w_high")):
                hi52_pct = (float(close) / float(row["52w_high"]) - 1) * 100
            if not _safe(lo52_pct) and _safe(close) and _safe(row.get("52w_low")):
                lo52_pct = (float(close) / float(row["52w_low"]) - 1) * 100
 
            hi52_s = f"{float(hi52_pct):+.1f}%" if _safe(hi52_pct) else "N/A"
            lo52_s = f"{float(lo52_pct):+.1f}%" if _safe(lo52_pct) else "N/A"
 
            rows_html += f"""
            <tr class="srow{new_cls}"
              data-sym="{sym}" data-close="{_r(close)}" data-rs="{_r(rs)}"
              data-ema10="{_r(ema10)}" data-tmc="{_r(tmc)}" data-tv="{_r(tv)}"
              data-indgrp="{ind_grp}" data-ind="">
              <td>
                <a class="sym-tag" style="background:var(--amber-lt);border-color:var(--amber-mid);color:var(--amber)"
                   href="{link}" target="_blank" rel="noopener">{sym}<span class="ib-badge">IB</span>{_new_star(is_new)}</a>
              </td>
              <td class="r" style="font-family:var(--mono)">{close_s}</td>
              <td class="r"><span class="pill pill-green">{ema10_s}</span></td>
              <td class="r"><span class="pill pill-amber">{rs_s}</span></td>
              <td class="r" style="font-family:var(--mono);color:var(--emerald);font-weight:600">{lo52_s}</td>
              <td class="r" style="font-family:var(--mono);color:var(--amber);font-weight:600">{hi52_s}</td>
              <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tmc_s}</td>
              <td class="r" style="font-family:var(--mono);color:var(--muted);font-size:.77rem">{tv_s}</td>
              <td style="color:var(--muted);font-size:.78rem">{ind_grp}</td>
            </tr>"""
 
    n_new = sum(1 for _, r in rocket.iterrows()
                if str(r.get("symbol","")).replace(".NS","") not in known) if n_rocket > 0 else 0
    hit_rate = f"{100*n_rocket/n_passing:.1f}%" if n_passing > 0 else "N/A"
 
    html  = _html_head(f"Momentum Alpha — Rocket Stocks — {date_display}",
                       "var(--amber)", "var(--red)")
    html += f"""
<header>
  <div class="hdr-left">
    <div class="brand">
      <div class="brand-dot" style="background:var(--amber)"></div>
      <span class="brand-name">Momentum Alpha · Rocket Stocks</span>
    </div>
    <h1>Rocket Stocks</h1>
    <p class="hdr-sub">All 8 Minervini conditions + Inside Bar coiling setup · NSE India · {date_display}</p>
    <div class="badge-row">
      <span class="hdr-badge" style="background:var(--amber-lt);border-color:var(--amber-mid);color:var(--amber)">✓ 8 Minervini Conditions</span>
      <span class="hdr-badge" style="background:var(--amber-lt);border-color:var(--amber-mid);color:var(--amber)">✓ Inside Bar</span>
      {"<span class='hdr-badge' style='background:var(--new-bg);border-color:var(--new-border);color:var(--new-text)'>✦ " + str(n_new) + " New Stocks</span>" if n_new else ""}
    </div>
  </div>
  <div class="date-pill" style="background:var(--amber-lt);border-color:var(--amber-mid);color:var(--amber)">{date_display}</div>
</header>
 
<div class="kpi-strip">
  <div class="kpi" style="--accent:var(--amber)">
    <div class="kpi-lbl">Rocket Stocks</div>
    <div class="kpi-val">{n_rocket}</div>
    <div class="kpi-hint">inside bar coiling</div>
  </div>
  <div class="kpi" style="--accent:var(--indigo)">
    <div class="kpi-lbl">Total Passing</div>
    <div class="kpi-val">{n_passing}</div>
    <div class="kpi-hint">all 8 conditions</div>
  </div>
  <div class="kpi" style="--accent:var(--emerald)">
    <div class="kpi-lbl">IB Hit Rate</div>
    <div class="kpi-val">{hit_rate}</div>
    <div class="kpi-hint">inside bar frequency</div>
  </div>
  {"<div class='kpi' style='--accent:var(--new-text)'><div class='kpi-lbl'>New Appearances</div><div class='kpi-val'>" + str(n_new) + "</div><div class='kpi-hint'>first time in 10 days</div></div>" if n_new else ""}
</div>
 
<div class="callout">
  <strong style="color:var(--amber)">Inside Bar:</strong>
  Today's high &lt; yesterday's high <strong>AND</strong> today's low &gt; yesterday's low —
  price compression inside a strong uptrend. Potential coiling setup before breakout.
</div>
 
<div class="table-sec" style="padding-top:1.1rem">
  <div class="tbl-head">
    <div>
      <span class="tbl-title">Rocket Stocks</span>
      <span class="tbl-count tbl-title">[{n_rocket}]</span>
    </div>
    <div class="controls">
      <div class="legend-row">
        <div class="leg"><div class="leg-dot" style="background:var(--new-border)"></div>✦ New (10-day)</div>
      </div>
      <input class="search" id="searchInput" type="text"
             placeholder="Search symbol / industry…" oninput="filterRows()"/>
    </div>
  </div>
  <div class="tbl-outer">
    <table id="mainTable">
      <thead><tr>
        <th data-col="sym"  data-type="str">Symbol<i class="si"></i></th>
        <th class="r" data-col="close" data-type="num">Close ₹<i class="si"></i></th>
        <th class="r" data-col="ema10" data-type="num">EMA10 ₹<i class="si"></i></th>
        <th class="r" data-col="rs"    data-type="num">RS %ile<i class="si"></i></th>
        <th class="r">% above 52W Low</th>
        <th class="r">% from 52W High</th>
        <th class="r" data-col="tmc"   data-type="num">Mkt Cap<i class="si"></i></th>
        <th class="r" data-col="tv"    data-type="num">Traded Val<i class="si"></i></th>
        <th data-col="indgrp" data-type="str">Industry Group<i class="si"></i></th>
      </tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
</div>
 
<footer>Data: NSE India &amp; Yahoo Finance · Generated {date_display} · For informational purposes only · Not financial advice</footer>
 
<script>
{_FILTER_JS}
{_TABLE_SORT_JS}
</script>
</body></html>"""
 
    out_path.write_text(html, encoding="utf-8")
    logger.info("Rocket dashboard → %s  (%d stocks)", out_path, n_rocket)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  MAIN INDEX PAGE
# ─────────────────────────────────────────────────────────────────────────────
 
def build_main_index(
    passing_path="passing_dashboard.html",
    elite_path="elite_dashboard.html",
    volume_path="volume_action_dashboard.html",
    rocket_path="rocket_dashboard.html",
    out_path="index.html"
):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Momentum Alpha Dashboard</title>
<link href="{_GOOGLE_FONTS}" rel="stylesheet"/>
<style>
:root {{
  --bg:#f7f8fc; --surface:#fff; --border:#e2e6f0;
  --text:#0f1629; --muted:#5a6282;
  --sans:'Outfit',system-ui,sans-serif; --mono:'DM Mono',monospace;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;padding:2.5rem}}
.topbar{{height:3px;background:linear-gradient(90deg,#4f46e5,#06b6d4);margin:-2.5rem -2.5rem 2rem;}}
h1{{font-size:1.7rem;font-weight:700;letter-spacing:-.03em;margin-bottom:.35rem}}
.sub{{color:var(--muted);font-size:.85rem;margin-bottom:2rem;font-family:var(--mono)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;
       padding:1.4rem 1.6rem;position:relative;overflow:hidden;transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.07)}}
.card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--c)}}
.card-icon{{font-size:1.4rem;margin-bottom:.6rem}}
.card h2{{font-size:1rem;font-weight:700;letter-spacing:-.01em;margin-bottom:.3rem}}
.card p{{font-size:.78rem;color:var(--muted);margin-bottom:1rem;line-height:1.5}}
.card a{{display:inline-flex;align-items:center;gap:.35rem;padding:.38rem .95rem;
         font-family:var(--mono);font-size:.72rem;font-weight:500;border-radius:8px;
         border:1px solid;text-decoration:none;transition:background .14s}}
</style>
</head>
<body>
<div class="topbar"></div>
<h1>Momentum Alpha</h1>
<p class="sub">// NSE Minervini Trend Scanner · India</p>
<div class="grid">
  <div class="card" style="--c:#4f46e5">
    <div class="card-icon">📊</div>
    <h2>Passing Stocks</h2>
    <p>All 8 Minervini conditions met — the core universe of momentum candidates.</p>
    <a href="{passing_path}" style="background:#eef0fd;border-color:#c7d2fe;color:#4f46e5">
      Open Dashboard →
    </a>
  </div>
  <div class="card" style="--c:#059669">
    <div class="card-icon">⭐</div>
    <h2>Elite Stocks</h2>
    <p>All 8 conditions + Close above EMA10 — highest-quality momentum stocks.</p>
    <a href="{elite_path}" style="background:#ecfdf5;border-color:#a7f3d0;color:#059669">
      Open Dashboard →
    </a>
  </div>
  <div class="card" style="--c:#2563eb">
    <div class="card-icon">📈</div>
    <h2>Volume Action</h2>
    <p>Pocket pivot volume events — institutional accumulation signals.</p>
    <a href="{volume_path}" style="background:#eff6ff;border-color:#bfdbfe;color:#2563eb">
      Open Dashboard →
    </a>
  </div>
  <div class="card" style="--c:#d97706">
    <div class="card-icon">🚀</div>
    <h2>Rocket Stocks</h2>
    <p>All 8 conditions + Inside Bar — price coiling for potential breakout.</p>
    <a href="{rocket_path}" style="background:#fffbeb;border-color:#fde68a;color:#d97706">
      Open Dashboard →
    </a>
  </div>
</div>
</body></html>"""
 
    Path(out_path).write_text(html, encoding="utf-8")
    logger.info("Main index page → %s", out_path)
 
