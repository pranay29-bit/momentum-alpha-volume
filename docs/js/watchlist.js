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
  setDoc,
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
const addSymbolInput = document.getElementById("addSymbolInput");
const addSymbolBtn   = document.getElementById("addSymbolBtn");
const addSymbolMsg   = document.getElementById("addSymbolMsg");
const changeHeader   = document.getElementById("changeHeader");
const breadthAdvN    = document.getElementById("breadthAdvN");
const breadthDecN    = document.getElementById("breadthDecN");
const breadthFlatN   = document.getElementById("breadthFlatN");
const breadthNoDataN = document.getElementById("breadthNoDataN");
const breadthBarAdv  = document.getElementById("breadthBarAdv");
const breadthBarDec  = document.getElementById("breadthBarDec");
const breadthBarFlat = document.getElementById("breadthBarFlat");
const breadthVerdict = document.getElementById("breadthVerdict");

let currentUid = null;
let unsubWatchlist = null;
let items = []; // [{symbol, currentPrice, industryGroup, industry}]
let changeSortDir = null; // null = default (by symbol), "asc" | "desc" = by changePercent

function loadLocalMeta() {
  try { return JSON.parse(localStorage.getItem(LOCAL_META_KEY) || "{}"); }
  catch { return {}; }
}

function loadLocal() {
  try { return new Set(JSON.parse(localStorage.getItem(LOCAL_KEY) || "[]")); }
  catch { return new Set(); }
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

function addLocal(symbol) {
  try {
    const symbols = new Set(JSON.parse(localStorage.getItem(LOCAL_KEY) || "[]"));
    symbols.add(symbol);
    localStorage.setItem(LOCAL_KEY, JSON.stringify(Array.from(symbols)));
    const meta = loadLocalMeta();
    if (!meta[symbol]) meta[symbol] = { currentPrice: null, industryGroup: "", industry: "" };
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

function computeBreadth(list) {
  const EPS = 0.05; // % — treat tiny wiggles as unchanged, not a real advance/decline
  let adv = 0, dec = 0, flat = 0, noData = 0;
  list.forEach((it) => {
    const cp = Number(it.changePercent);
    if (!Number.isFinite(cp)) { noData++; return; }
    if (cp > EPS) adv++;
    else if (cp < -EPS) dec++;
    else flat++;
  });
  return { adv, dec, flat, noData, tracked: adv + dec + flat };
}

function renderBreadth() {
  const { adv, dec, flat, noData, tracked } = computeBreadth(items);

  breadthAdvN.textContent = adv;
  breadthDecN.textContent = dec;
  breadthFlatN.textContent = flat;
  breadthNoDataN.textContent = noData;

  const total = adv + dec + flat + noData;
  if (total === 0) {
    breadthBarAdv.style.width = "0%";
    breadthBarDec.style.width = "0%";
    breadthBarFlat.style.width = "100%";
    breadthVerdict.innerHTML = `<span class="tag mixed">No data</span>Your watchlist is empty — star some stocks to see breadth here.`;
    return;
  }

  breadthBarAdv.style.width = `${(adv / total) * 100}%`;
  breadthBarDec.style.width = `${(dec / total) * 100}%`;
  breadthBarFlat.style.width = `${((flat + noData) / total) * 100}%`;

  if (tracked === 0) {
    breadthVerdict.innerHTML = `<span class="tag mixed">No data</span>Waiting for the next scheduled price refresh — breadth will fill in once prices update.`;
    return;
  }

  // Net breadth: -1 (everything down) to +1 (everything up), ignoring
  // names still waiting on a price refresh.
  const score = (adv - dec) / tracked;
  const advPct = Math.round((adv / tracked) * 100);
  const staleNote = noData > 0 ? ` (${noData} still waiting on a price refresh)` : "";

  let tagClass, tagText, verdict;
  if (score >= 0.4) {
    tagClass = "bullish";
    tagText = "Bullish tape";
    verdict = `${adv} of ${tracked} watchlist names (${advPct}%) are trading higher today, with only ${dec} down${staleNote}. Breadth is broadly positive — the tape is supportive of taking fresh long setups, though this only reflects your own watchlist, not the full market.`;
  } else if (score <= -0.4) {
    tagClass = "bearish";
    tagText = "Bearish tape";
    verdict = `${dec} of ${tracked} watchlist names are trading lower today against just ${adv} advancing${staleNote}. Breadth is broadly negative — this is usually a day to be defensive: tighten stops on existing longs and hold off on fresh breakout entries until breadth improves.`;
  } else {
    tagClass = "mixed";
    tagText = "Mixed tape";
    verdict = `${adv} up vs ${dec} down out of ${tracked} tracked names${staleNote} — advances and declines are roughly balanced. No clear edge from breadth alone; be selective, favor your strongest setups, and size down on new entries.`;
  }

  breadthVerdict.innerHTML = `<span class="tag ${tagClass}">${tagText}</span>${verdict}`;
}

function render() {
  countBadgeNum.textContent = items.length;
  renderBreadth();

  if (!items.length) {
    tableBody.innerHTML = `<tr class="wl-empty-row"><td colspan="7">No stocks in your watchlist yet — click the ☆ next to any symbol on a dashboard to add it here.</td></tr>`;
    return;
  }

  changeHeader.classList.toggle("sort-active", changeSortDir !== null);
  changeHeader.querySelector(".sort-i").textContent =
    changeSortDir === "asc" ? "↑" : changeSortDir === "desc" ? "↓" : "⇅";

  const sorted = items.slice().sort((a, b) => {
    if (changeSortDir === "asc" || changeSortDir === "desc") {
      const av = Number.isFinite(Number(a.changePercent)) ? Number(a.changePercent) : -Infinity;
      const bv = Number.isFinite(Number(b.changePercent)) ? Number(b.changePercent) : -Infinity;
      return changeSortDir === "asc" ? av - bv : bv - av;
    }
    return a.symbol.localeCompare(b.symbol);
  });

  tableBody.innerHTML = sorted
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

function showAddMsg(text, isError) {
  addSymbolMsg.textContent = text;
  addSymbolMsg.style.color = isError ? "var(--red)" : "var(--subtle)";
  if (text) setTimeout(() => { if (addSymbolMsg.textContent === text) addSymbolMsg.textContent = ""; }, 3000);
}

async function addSymbol() {
  const raw = (addSymbolInput.value || "").trim().toUpperCase();
  if (!raw) return;
  // Strip a trailing .NS/.BO if someone pastes the full Yahoo ticker —
  // the watchlist stores the same plain display symbol dashboards use.
  const symbol = raw.replace(/\.(NS|BO)$/, "");

  const alreadyIn = currentUid
    ? items.some((it) => it.symbol === symbol)
    : loadLocal().has(symbol);
  if (alreadyIn) {
    showAddMsg(`${symbol} is already in your watchlist.`, true);
    return;
  }

  addSymbolBtn.disabled = true;
  try {
    if (currentUid) {
      await setDoc(doc(db, "users", currentUid, "watchlist", symbol), {
        symbol,
        industryGroup: "",
        industry: "",
        currentPrice: null,
        addedAt: Date.now()
      }, { merge: true });
      // onSnapshot will pick this up and re-render automatically.
    } else {
      addLocal(symbol);
      items = loadLocalItems();
      render();
    }
    addSymbolInput.value = "";
    showAddMsg(`Added ${symbol}. Price and industry fill in on the next scheduled refresh.`, false);
  } catch (err) {
    console.error(err);
    showAddMsg(`Could not add ${symbol}.`, true);
  } finally {
    addSymbolBtn.disabled = false;
  }
}

addSymbolBtn.addEventListener("click", addSymbol);
addSymbolInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") addSymbol();
});

changeHeader.addEventListener("click", () => {
  changeSortDir = changeSortDir === null ? "desc" : changeSortDir === "desc" ? "asc" : null;
  render();
});

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
