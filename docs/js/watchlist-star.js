// docs/js/watchlist-star.js
//
// Shared ☆ / ★ toggle used on every generated scan dashboard (Momentum,
// Elite, Volume, Rocket, New RS High, Stage 4, SME Momentum, SME Elite).
//
// Anonymous visitors: stars are kept in localStorage only (per-browser,
// no live price refresh).
// Logged-in visitors: stars are written to Firestore under
// users/{uid}/watchlist/{symbol} — the same collection the Watchlist page
// (watchlist.html) reads, and the same collection scripts/update-prices.js
// refreshes on a schedule, so a starred stock's current price keeps
// updating live exactly like an Open Position.
//
// Login itself happens on the Watchlist / Position Tracker pages — this
// module only needs to know whether a session already exists so it can
// decide whether to sync to Firestore or fall back to localStorage.

import { db, auth, onAuthStateChanged } from "./firebase.js";
import {
  doc,
  setDoc,
  deleteDoc,
  collection,
  onSnapshot
} from "https://www.gstatic.com/firebasejs/11.9.0/firebase-firestore.js";

const LOCAL_KEY = "wl_symbols";
const LOCAL_META_KEY = "wl_meta";

function loadLocal() {
  try {
    return new Set(JSON.parse(localStorage.getItem(LOCAL_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveLocal(set) {
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(Array.from(set)));
  } catch {
    /* ignore quota / private-mode errors */
  }
}

function saveLocalMeta(symbol, meta) {
  try {
    const all = JSON.parse(localStorage.getItem(LOCAL_META_KEY) || "{}");
    all[symbol] = meta;
    localStorage.setItem(LOCAL_META_KEY, JSON.stringify(all));
  } catch {
    /* ignore */
  }
}

let currentUid = null;
let watchedSymbols = loadLocal();
let unsubWatchlist = null;

function paintStars() {
  document.querySelectorAll(".wl-star").forEach((btn) => {
    const tr = btn.closest("tr");
    const sym = tr ? tr.dataset.sym : "";
    const on = watchedSymbols.has(sym);
    btn.classList.toggle("is-active", on);
    btn.textContent = on ? "★" : "☆";
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.title = on ? "Remove from Watchlist" : "Add to Watchlist";
  });
}

async function toggleStar(btn) {
  const tr = btn.closest("tr");
  if (!tr) return;

  const sym     = tr.dataset.sym || "";
  const close   = tr.dataset.close;
  const indgrp  = tr.dataset.indgrp || "";
  const ind     = tr.dataset.ind || "";
  if (!sym) return;

  const isOn = watchedSymbols.has(sym);

  if (isOn) {
    watchedSymbols.delete(sym);
  } else {
    watchedSymbols.add(sym);
    saveLocalMeta(sym, {
      currentPrice: close && !isNaN(parseFloat(close)) ? parseFloat(close) : null,
      industryGroup: indgrp,
      industry: ind
    });
  }
  saveLocal(watchedSymbols);
  paintStars();

  if (currentUid) {
    const ref = doc(db, "users", currentUid, "watchlist", sym);
    try {
      if (isOn) {
        await deleteDoc(ref);
      } else {
        await setDoc(
          ref,
          {
            symbol: sym,
            industryGroup: indgrp,
            industry: ind,
            currentPrice: close && !isNaN(parseFloat(close)) ? parseFloat(close) : null,
            addedAt: Date.now()
          },
          { merge: true }
        );
      }
    } catch (err) {
      console.error("Could not sync watchlist star:", err);
    }
  }
}

// Exposed for the inline onclick="toggleStar(this)" attributes rendered
// by scanner/dashboard.py's _star_cell().
window.toggleStar = toggleStar;

document.addEventListener("DOMContentLoaded", paintStars);
// In case this script executes after DOMContentLoaded has already fired
// (it's loaded as a module, deferred by default).
paintStars();

onAuthStateChanged(auth, (user) => {
  if (unsubWatchlist) {
    unsubWatchlist();
    unsubWatchlist = null;
  }
  currentUid = user ? user.uid : null;

  if (currentUid) {
    const ref = collection(db, "users", currentUid, "watchlist");
    unsubWatchlist = onSnapshot(ref, (snap) => {
      watchedSymbols = new Set(snap.docs.map((d) => d.id));
      saveLocal(watchedSymbols);
      paintStars();
    });
  }
});
