// docs/js/watchlist.js
//
// Powers watchlist.html. Mirrors the pattern used by position-tracker.js:
//   • Logged out  -> read/write localStorage only, no live price refresh.
//   • Logged in   -> subscribe to users/{uid}/watchlist via onSnapshot, so
//                    the table re-renders the instant scripts/update-prices.js
//                    (run on the same schedule as Open Positions) writes a
//                    new currentPrice into Firestore. No polling needed.

import { db, auth, login, logout, onAuthStateChanged } from "./firebase.js";
import {
  collection,
  doc,
  deleteDoc,
  onSnapshot,
  query,
  orderBy
} from "https://www.gstatic.com/firebasejs/11.9.0/firebase-firestore.js";

const LOCAL_KEY = "wl_symbols";
const LOCAL_META_KEY = "wl_meta"; // symbol -> {currentPrice, industryGroup, industry}

const loginBtn      = document.getElementById("loginBtn");
const loginStatus    = document.getElementById("loginStatus");
const tableBody      = document.getElementById("wlTableBody");
const countBadgeNum  = document.querySelector("#wlCountBadge .n");

let currentUid = null;
let unsubWatchlist = null;
let items = []; // [{symbol, currentPrice, industryGroup, industry}]

function loadLocalMeta() {
  try { return JSON.parse(localStorage.getItem(LOCAL_META_KEY) || "{}"); }
  catch { return {}; }
}

function loadLocalItems() {
  let symbols = [];
  try { symbols = JSON.parse(localStorage.getItem(LOCAL_KEY) || "[]"); }
  catch { symbols = []; }
  const meta = loadLocalMeta();
  return symbols.map((symbol) => ({
    symbol,
    currentPrice: meta[symbol]?.currentPrice ?? null,
    previousClose: meta[symbol]?.previousClose ?? null,
    change: meta[symbol]?.change ?? null,
    changePercent: meta[symbol]?.changePercent ?? null,
    industryGroup: meta[symbol]?.industryGroup ?? "—",
    industry: meta[symbol]?.industry ?? "—"
  }));
}

function removeLocal(symbol) {
  try {
    const symbols = JSON.parse(localStorage.getItem(LOCAL_KEY) || "[]").filter((s) => s !== symbol);
    localStorage.setItem(LOCAL_KEY, JSON.stringify(symbols));
    const meta = loadLocalMeta();
    delete meta[symbol];
    localStorage.setItem(LOCAL_META_KEY, JSON.stringify(meta));
  } catch {
    /* ignore */
  }
}

function fmtPrice(p) {
  const n = Number(p);
  return Number.isFinite(n) && n > 0 ? `₹${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";
}

function pnlClass(value) {
  if (value > 0.001) return "pnl-pos";
  if (value < -0.001) return "pnl-neg";
  return "pnl-flat";
}

function fmtChange(change, changePercent) {
  if (!Number.isFinite(Number(change)) || !Number.isFinite(Number(changePercent))) {
    return `<span class="pnl-flat">—</span>`;
  }
  const c = Number(change);
  const pct = Number(changePercent);
  const sign = c > 0 ? "+" : "";
  return `<span class="${pnlClass(c)}">${sign}${c.toFixed(2)} (${sign}${pct.toFixed(2)}%)</span>`;
}

function render() {
  countBadgeNum.textContent = items.length;

  if (!items.length) {
    tableBody.innerHTML = `<tr class="wl-empty-row"><td colspan="7">No stocks in your watchlist yet — click the ☆ next to any symbol on a dashboard to add it here.</td></tr>`;
    return;
  }

  tableBody.innerHTML = items
    .slice()
    .sort((a, b) => a.symbol.localeCompare(b.symbol))
    .map(
      (it) => `
      <tr data-sym="${it.symbol}">
        <td>★</td>
        <td style="font-family:var(--mono);font-weight:600">${it.symbol}</td>
        <td>${fmtPrice(it.currentPrice)}</td>
        <td>${fmtChange(it.change, it.changePercent)}</td>
        <td>${it.industryGroup || "—"}</td>
        <td>${it.industry || "—"}</td>
        <td><button class="wl-remove-btn" data-sym="${it.symbol}">✕ Remove</button></td>
      </tr>`
    )
    .join("");

  tableBody.querySelectorAll(".wl-remove-btn").forEach((btn) => {
    btn.addEventListener("click", () => removeSymbol(btn.dataset.sym));
  });
}

async function removeSymbol(symbol) {
  removeLocal(symbol);
  if (currentUid) {
    try {
      await deleteDoc(doc(db, "users", currentUid, "watchlist", symbol));
    } catch (err) {
      console.error("Could not remove from Firestore:", err);
    }
  } else {
    items = items.filter((it) => it.symbol !== symbol);
    render();
  }
}

function subscribeToWatchlist(uid) {
  const ref = collection(db, "users", uid, "watchlist");
  const q = query(ref, orderBy("symbol"));
  tableBody.innerHTML = `<tr class="wl-empty-row"><td colspan="7">Loading…</td></tr>`;

  unsubWatchlist = onSnapshot(
    q,
    (snap) => {
      items = snap.docs.map((d) => {
        const data = d.data();
        return {
          symbol: data.symbol || d.id,
          currentPrice: data.currentPrice ?? null,
          previousClose: data.previousClose ?? null,
          change: data.change ?? null,
          changePercent: data.changePercent ?? null,
          industryGroup: data.industryGroup || "—",
          industry: data.industry || "—"
        };
      });
      render();
    },
    (err) => {
      console.error(err);
      tableBody.innerHTML = `<tr class="wl-empty-row"><td colspan="7">Could not load watchlist (check Firestore rules for users/{uid}/watchlist).</td></tr>`;
    }
  );
}

loginBtn.onclick = async () => {
  if (auth.currentUser) {
    await logout();
  } else {
    try {
      await login();
    } catch (err) {
      console.error(err);
      alert("Login failed. Please try again.");
    }
  }
};

onAuthStateChanged(auth, (user) => {
  if (unsubWatchlist) { unsubWatchlist(); unsubWatchlist = null; }

  if (user) {
    currentUid = user.uid;
    loginBtn.textContent = `Logout (${user.displayName || user.email})`;
    loginStatus.textContent =
      "Logged in — your watchlist syncs across devices and Current Price refreshes automatically on the scheduled server job.";
    subscribeToWatchlist(user.uid);
  } else {
    currentUid = null;
    loginBtn.textContent = "Login with Google";
    loginStatus.textContent =
      "Login to sync your watchlist across devices and get live current-price refreshes (every scheduled run) like Open Positions. " +
      "Without login, stars are saved to this browser only and the price shown is the one captured at the moment you starred it.";
    items = loadLocalItems();
    render();
  }
});

// ── TradingView export — same plain "SYMBOL,SYMBOL,…" format used by the
// _tv_export_bar() on every scan dashboard, so lists exported from either
// place paste identically into TradingView. ──────────────────────────────
function _tvSymbolList() {
  return items.map((it) => (it.symbol || "").toUpperCase()).filter(Boolean);
}

window.downloadTVList = function () {
  const syms = _tvSymbolList();
  if (!syms.length) { alert("No symbols to export."); return; }
  const blob = new Blob([syms.join(",")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "tradingview_watchlist.txt";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

window.copyTVList = function () {
  const syms = _tvSymbolList();
  if (!syms.length) { alert("No symbols to copy."); return; }
  const text = syms.join(",");
  const btn = document.getElementById("tvCopyBtn");
  const done = () => {
    if (!btn) return;
    const orig = btn.dataset.origLabel || btn.textContent;
    btn.dataset.origLabel = orig;
    btn.textContent = "✓ Copied!";
    setTimeout(() => { btn.textContent = orig; }, 1600);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done).catch(() => _tvFallbackCopy(text, done));
  } else {
    _tvFallbackCopy(text, done);
  }
};

function _tvFallbackCopy(text, done) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand("copy"); done(); } catch (e) { alert("Copy failed — please copy manually."); }
  ta.remove();
}

// Initial paint for the logged-out/default case, before onAuthStateChanged
// fires for the first time.
items = loadLocalItems();
render();
