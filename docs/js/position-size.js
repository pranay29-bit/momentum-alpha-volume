import { db, auth, login, logout, onAuthStateChanged } from "./firebase.js";

import {
  collection,
  addDoc,
  doc,
  getDoc,
  setDoc,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/11.9.0/firebase-firestore.js";

const loginBtn = document.getElementById("loginBtn");
const addBtn = document.getElementById("addBtn");
const addStatus = document.getElementById("addStatus");
const settingsStatus = document.getElementById("settingsStatus");

const portfolioSizeInput = document.getElementById("portfolioSize");
const riskTypeSelect = document.getElementById("riskType");
const riskValueInput = document.getElementById("riskValue");
const symbolInput = document.getElementById("symbol");
const dateBoughtInput = document.getElementById("dateBought");
const entryInput = document.getElementById("entry");
const stopInput = document.getElementById("stop");

// Default Date Bought to today, but the user can change it freely.
dateBoughtInput.value = new Date().toISOString().slice(0, 10);

const previewBox = document.getElementById("previewBox");
const previewRiskAmount = document.getElementById("previewRiskAmount");
const previewRiskPerShare = document.getElementById("previewRiskPerShare");
const previewRiskPct = document.getElementById("previewRiskPct");
const previewQty = document.getElementById("previewQty");
const previewCapital = document.getElementById("previewCapital");

// Never let a single position eat more than this % of the portfolio in
// capital terms, regardless of how small the risk-based qty's per-share
// risk makes it look. A stock with a very tight stop can otherwise size
// up to an enormous, dangerously concentrated position even though its
// *risk* in rupee terms looks small — this caps that independently.
const MAX_CAPITAL_PCT = 10;

// Small warning note, inserted dynamically right after the preview box —
// built in JS rather than assumed to exist in the HTML, so this doesn't
// depend on markup this file doesn't control.
const capNote = document.createElement("div");
capNote.id = "capitalCapNote";
capNote.style.cssText =
  "display:none;margin-top:.6rem;padding:.6rem .8rem;border-radius:8px;" +
  "background:#fffbeb;border:1px solid #fde68a;color:#b45309;" +
  "font-size:.8rem;line-height:1.4;";
previewBox.insertAdjacentElement("afterend", capNote);

let settingsSaveTimer = null;

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

onAuthStateChanged(auth, async (user) => {
  if (user) {
    loginBtn.textContent = `Logout (${user.displayName || user.email})`;
    await loadSettings(user.uid);
  } else {
    loginBtn.textContent = "Login with Google";
  }
});

// ── Persistent settings: portfolio size & risk type/value stay fixed
// until you explicitly change them — saved to Firestore so they also
// show up on the Position Tracker page and persist across sessions. ─────
async function loadSettings(uid) {
  try {
    const snap = await getDoc(doc(db, "users", uid));
    if (snap.exists()) {
      const data = snap.data();
      if (data.portfolioSize) portfolioSizeInput.value = data.portfolioSize;
      if (data.riskType) riskTypeSelect.value = data.riskType;
      if (data.riskValue) riskValueInput.value = data.riskValue;
      settingsStatus.textContent = "Loaded your saved portfolio settings.";
      calculate();
    }
  } catch (err) {
    console.error(err);
  }
}

function saveSettingsDebounced() {
  if (!auth.currentUser) return;
  clearTimeout(settingsSaveTimer);
  settingsStatus.textContent = "Saving…";
  settingsSaveTimer = setTimeout(async () => {
    try {
      await setDoc(doc(db, "users", auth.currentUser.uid), {
        portfolioSize: Number(portfolioSizeInput.value) || 0,
        riskType: riskTypeSelect.value,
        riskValue: Number(riskValueInput.value) || 0,
        updatedAt: serverTimestamp()
      }, { merge: true });
      settingsStatus.textContent = "Saved — this stays fixed until you change it again.";
    } catch (err) {
      console.error(err);
      settingsStatus.textContent = "Could not save settings.";
    }
  }, 600); // debounce so we don't write on every keystroke
}

[portfolioSizeInput, riskTypeSelect, riskValueInput].forEach((el) => {
  el.addEventListener("input", saveSettingsDebounced);
});

// ── Live calculation, recomputed on every keystroke ──────────────────────
function calculate() {
  const portfolio = Number(portfolioSizeInput.value);
  const riskType = riskTypeSelect.value; // "percent" | "absolute"
  const riskValue = Number(riskValueInput.value);
  const entry = Number(entryInput.value);
  const stop = Number(stopInput.value);

  if (!(portfolio > 0) || !(riskValue > 0) || !(entry > stop)) {
    previewBox.style.display = "none";
    capNote.style.display = "none";
    return null;
  }

  const riskAmount = riskType === "percent"
    ? (portfolio * riskValue) / 100
    : riskValue;

  const riskPerShare = entry - stop;
  const riskPct = (riskPerShare / entry) * 100; // Entry-SL distance, in %

  // Risk-based sizing (existing logic): how many shares does the risk
  // budget alone allow?
  const riskBasedQty = Math.floor(riskAmount / riskPerShare);

  // Capital cap: how many shares can we buy before this position alone
  // would exceed MAX_CAPITAL_PCT of the portfolio?
  const maxCapital = (portfolio * MAX_CAPITAL_PCT) / 100;
  const capCappedQty = Math.floor(maxCapital / entry);

  // Whichever is smaller wins — we never violate either limit.
  const qty = Math.max(0, Math.min(riskBasedQty, capCappedQty));
  const cappedByCapital = capCappedQty < riskBasedQty;

  const capitalRequired = qty * entry;
  const capitalPct = (capitalRequired / portfolio) * 100;

  previewBox.style.display = "flex";
  previewRiskAmount.textContent = formatINR(riskAmount);
  previewRiskPerShare.textContent = riskPerShare.toFixed(2);
  previewRiskPct.textContent = riskPct.toFixed(2) + "%";
  previewQty.textContent = qty;
  previewCapital.textContent = `${formatINR(capitalRequired)} (${capitalPct.toFixed(1)}% of portfolio)`;

  if (cappedByCapital && riskBasedQty > 0) {
    const uncappedCapitalPct = (riskBasedQty * entry / portfolio) * 100;
    capNote.textContent =
      `⚠️ Qty reduced from ${riskBasedQty} to ${qty} to stay within the ${MAX_CAPITAL_PCT}% ` +
      `capital cap — the risk-based quantity alone would have used ${uncappedCapitalPct.toFixed(1)}% ` +
      `of your portfolio in this one position.`;
    capNote.style.display = "block";
  } else {
    capNote.style.display = "none";
  }

  return { riskAmount, riskPerShare, riskPct, qty, capitalRequired, capitalPct, riskBasedQty, cappedByCapital };
}

[portfolioSizeInput, riskTypeSelect, riskValueInput, entryInput, stopInput]
  .forEach((el) => el.addEventListener("input", calculate));

addBtn.onclick = async () => {
  if (!auth.currentUser) {
    alert("Login first");
    return;
  }

  const symbol = symbolInput.value.trim().toUpperCase();
  if (!symbol) {
    alert("Enter a symbol");
    return;
  }
  const dateBought = dateBoughtInput.value;
  if (!dateBought) {
    alert("Enter the date you bought this position");
    return;
  }

  const result = calculate();
  if (!result) {
    alert("Enter a valid portfolio size, risk value, entry and stop loss (entry must be above stop).");
    return;
  }
  if (result.qty <= 0) {
    alert("Calculated quantity is 0 — your risk value may be too small for this stop distance.");
    return;
  }

  addBtn.disabled = true;
  addBtn.textContent = "Adding…";
  addStatus.textContent = "";

  try {
    const positionsRef = collection(db, "users", auth.currentUser.uid, "positions");

    await addDoc(positionsRef, {
      symbol,
      dateBought,
      entry: Number(entryInput.value),
      stop: Number(stopInput.value),
      qty: result.qty,
      riskPerShare: result.riskPerShare,
      riskAmount: result.riskAmount,
      riskPct: result.riskPct,
      capitalRequired: result.capitalRequired,
      capitalPct: result.capitalPct,
      cappedByCapital: result.cappedByCapital,
      currentPrice: Number(entryInput.value),
      createdAt: serverTimestamp()
    });

    addStatus.textContent = `Added ${symbol} · Qty ${result.qty}. View it on the Position Tracker page.`;
    symbolInput.value = "";
    entryInput.value = "";
    stopInput.value = "";
    dateBoughtInput.value = new Date().toISOString().slice(0, 10);
    previewBox.style.display = "none";
  } catch (err) {
    console.error(err);
    addStatus.textContent = "Could not add position. Please try again.";
  } finally {
    addBtn.disabled = false;
    addBtn.textContent = "+ Add Position";
  }
};

function formatINR(n) {
  return "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
