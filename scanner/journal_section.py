"""
journal_section.py
──────────────────
Drop this helper into scanner/ and call build_journal_html() from
dashboard.py to render the trading journal at the top of index.html.

The function reads  data/journal.csv  (committed to the repo) and
returns a self-contained HTML string that can be injected before the
scan-history section in the landing page.
"""

import csv
import os

# ── paths ──────────────────────────────────────────────────────────────
_REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_CSV  = os.path.join(_REPO_ROOT, "data", "journal.csv")

# ── CSS (inlined so it works without an extra stylesheet) ──────────────
_CSS = """
<style>
/* ── Journal Section ───────────────────────────────────────────── */
.journal-section {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border: 1px solid #334155;
  border-radius: 14px;
  padding: 28px 32px 24px;
  margin: 0 0 36px 0;
  color: #e2e8f0;
  box-shadow: 0 4px 32px rgba(0,0,0,.45);
}
.journal-section h2 {
  margin: 0 0 18px 0;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: .04em;
  color: #f8fafc;
  display: flex;
  align-items: center;
  gap: 10px;
}
.journal-section h2::before {
  content: "📒";
}
.journal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 22px;
}
.journal-meta-pill {
  background: #1e3a5f;
  border: 1px solid #2563eb44;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: .85rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.journal-meta-pill .pill-label {
  color: #94a3b8;
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.journal-meta-pill .pill-value {
  color: #38bdf8;
  font-weight: 700;
  font-size: 1rem;
}
.journal-table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #334155;
}
.journal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: .82rem;
  min-width: 700px;
}
.journal-table thead tr {
  background: #1e3a5f;
}
.journal-table thead th {
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: #93c5fd;
  letter-spacing: .04em;
  white-space: nowrap;
  border-bottom: 1px solid #334155;
}
.journal-table tbody tr {
  border-bottom: 1px solid #1e293b;
  transition: background .15s;
}
.journal-table tbody tr:hover {
  background: #1e3a5f66;
}
.journal-table tbody td {
  padding: 9px 14px;
  color: #cbd5e1;
  white-space: nowrap;
}
.journal-table tbody td:first-child { color: #64748b; }
/* profit colouring applied via JS below */
.profit-pos { color: #4ade80 !important; font-weight: 600; }
.profit-neg { color: #f87171 !important; font-weight: 600; }
.journal-empty {
  color: #64748b;
  font-style: italic;
  padding: 18px 0 4px;
  font-size: .88rem;
}
</style>
"""

# ── tiny JS to colour the Profit % column ─────────────────────────────
_JS = """
<script>
(function(){
  document.querySelectorAll('.journal-profit-cell').forEach(function(td){
    var v = parseFloat(td.textContent);
    if (!isNaN(v)) td.classList.add(v >= 0 ? 'profit-pos' : 'profit-neg');
  });
})();
</script>
"""


def _fmt(val: str) -> str:
    """Strip and return value, or em-dash if blank."""
    v = val.strip()
    return v if v else "—"


def build_journal_html(csv_path: str = JOURNAL_CSV) -> str:
    """
    Parse journal.csv and return a complete HTML snippet ready to inject
    at the top of the landing page body.

    CSV layout expected
    ───────────────────
    Row 0:  , Portfolio Size ,  <value>
    Row 1:  , Portfolio wise Risk per Trade ,  <value>
    Row 2:  (blank)
    Row 3+: header + data rows of the trade table

    The function is forgiving: if the file is missing or malformed it
    returns an empty string so the rest of the page still renders.
    """
    if not os.path.exists(csv_path):
        return ""

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
    except Exception:
        return ""

    # ── pull meta ────────────────────────────────────────────────────
    portfolio_size = "—"
    risk_per_trade = "—"
    for row in rows[:3]:
        cols = [c.strip() for c in row]
        if "Portfolio Size" in cols:
            idx = cols.index("Portfolio Size")
            if idx + 1 < len(cols):
                portfolio_size = _fmt(cols[idx + 1])
        if "Portfolio wise Risk per Trade" in cols:
            idx = cols.index("Portfolio wise Risk per Trade")
            if idx + 1 < len(cols):
                risk_per_trade = _fmt(cols[idx + 1])

    # ── locate header row ────────────────────────────────────────────
    header_idx = None
    for i, row in enumerate(rows):
        cols = [c.strip() for c in row]
        if "Stock Name" in cols:
            header_idx = i
            break

    # ── build trade table ────────────────────────────────────────────
    table_html = ""
    if header_idx is not None:
        header_row = [c.strip() for c in rows[header_idx]]
        # remove leading empty cells
        while header_row and not header_row[0]:
            header_row.pop(0)

        data_rows = []
        for row in rows[header_idx + 1:]:
            cols = [c.strip() for c in row]
            if any(cols):          # skip fully blank rows
                data_rows.append(cols)

        # profit % column index (last column named "Profit %")
        profit_col = None
        for j, h in enumerate(header_row):
            if "Profit" in h:
                profit_col = j

        th_cells = "".join(f"<th>{h}</th>" for h in header_row)
        thead = f"<thead><tr>{th_cells}</tr></thead>"

        tbody_rows = []
        for dr in data_rows:
            # pad row to header length
            while len(dr) < len(header_row):
                dr.append("")
            td_cells = []
            for j, h in enumerate(header_row):
                val = _fmt(dr[j]) if j < len(dr) else "—"
                cls = ' class="journal-profit-cell"' if j == profit_col else ""
                td_cells.append(f"<td{cls}>{val}</td>")
            tbody_rows.append("<tr>" + "".join(td_cells) + "</tr>")

        if tbody_rows:
            tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"
            table_html = (
                '<div class="journal-table-wrap">'
                f'<table class="journal-table">{thead}{tbody}</table>'
                "</div>"
            )
        else:
            table_html = (
                '<p class="journal-empty">'
                "No trades added yet — fill in the journal sheet and re-run the scanner."
                "</p>"
            )

    # ── format portfolio size nicely ─────────────────────────────────
    try:
        size_display = "₹{:,.0f}".format(float(portfolio_size.replace(",", "")))
    except ValueError:
        size_display = portfolio_size

    # ── assemble ─────────────────────────────────────────────────────
    html = f"""
{_CSS}
<section class="journal-section">
  <h2>Trading Journal</h2>
  <div class="journal-meta">
    <div class="journal-meta-pill">
      <span class="pill-label">Portfolio Size</span>
      <span class="pill-value">{size_display}</span>
    </div>
    <div class="journal-meta-pill">
      <span class="pill-label">Risk per Trade</span>
      <span class="pill-value">{risk_per_trade}</span>
    </div>
  </div>
  {table_html}
</section>
{_JS}
"""
    return html
