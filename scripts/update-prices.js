// scripts/update-prices.js
//
// Standalone script (no Cloud Functions, no Blaze plan needed) that:
//   1. Authenticates to Firestore using a service account key.
//   2. Reads every doc in the "positions" collection.
//   3. Fetches a live price per unique symbol from Yahoo Finance,
//      handling the crumb/cookie handshake Yahoo now requires.
//   4. Writes currentPrice back to Firestore.
//
// Run manually with:  node scripts/update-prices.js
// Run on a schedule via the GitHub Actions workflow in
// .github/workflows/update-prices.yml

const admin = require("firebase-admin");
const fs = require("fs");
const path = require("path");

// The service account JSON is provided as a GitHub Actions secret and
// written to this env var as a string (see the workflow file). For local
// testing, you can instead point GOOGLE_APPLICATION_CREDENTIALS at a
// downloaded service-account.json file and skip this block.
if (!admin.apps.length) {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount)
    });
  } else {
    // Falls back to GOOGLE_APPLICATION_CREDENTIALS env var pointing at a
    // local JSON key file, for testing on your own machine.
    admin.initializeApp();
  }
}

const db = admin.firestore();

// ── Yahoo Finance crumb/cookie handshake ──────────────────────────────────
let cachedCrumb = null;
let cachedCookie = null;

// Positions are stored with whatever the user typed into the Position Size
// Calculator (e.g. "PGIL", "reliance") — clean and suffix-free, which is
// what the UI displays. Yahoo Finance, however, requires the exchange
// suffix for NSE-listed tickers (PGIL.NS, not PGIL) or it 404s. Rather than
// changing what's stored/displayed everywhere else in the app, normalize
// only at the point of the Yahoo fetch: uppercase, and append ".NS" unless
// the symbol already carries a recognized exchange suffix (so a position
// someone deliberately entered as "SOMETICKER.BO" for BSE is left alone).
function toYahooSymbol(symbol) {
  const s = symbol.trim().toUpperCase();
  return /\.(NS|BO)$/.test(s) ? s : `${s}.NS`;
}

// ── Industry / Industry Group lookup ──────────────────────────────────────
// The watchlist stores plain display symbols (whatever _display_symbol()
// rendered on the dashboard — e.g. "RELIANCE", or a company name for bare
// numeric BSE SME codes). Industry classification for those already lives
// in data/NSE_Stocks.csv and data/SME_Stocks.csv, so rather than duplicate
// it we just look it up here at update time.
function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  if (!lines.length) return [];
  const headers = lines[0].split(",").map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    const row = {};
    headers.forEach((h, i) => { row[h] = (cells[i] || "").trim(); });
    return row;
  });
}

function loadIndustryLookup() {
  const lookup = new Map(); // uppercased symbol OR name -> {industryGroup, industry}
  const files = [
    { file: "data/NSE_Stocks.csv", keyCols: ["Symbol", "Name"] },
    { file: "data/SME_Stocks.csv", keyCols: ["Symbols", "Name"] }
  ];

  for (const { file, keyCols } of files) {
    const fullPath = path.join(__dirname, "..", file);
    if (!fs.existsSync(fullPath)) continue;
    const rows = parseCsv(fs.readFileSync(fullPath, "utf-8"));
    for (const row of rows) {
      const info = {
        industryGroup: row["Industry Group"] || "",
        industry: row["Industry"] || ""
      };
      for (const col of keyCols) {
        const key = (row[col] || "").trim().toUpperCase();
        if (key) lookup.set(key, info);
      }
    }
  }
  return lookup;
}

function lookupIndustry(lookup, symbol) {
  return lookup.get(symbol.trim().toUpperCase()) || { industryGroup: "", industry: "" };
}

async function getCrumbAndCookie() {
  if (cachedCrumb && cachedCookie) return { crumb: cachedCrumb, cookie: cachedCookie };

  const cookieRes = await fetch("https://fc.yahoo.com", {
    headers: { "User-Agent": "Mozilla/5.0" }
  });
  const setCookie = cookieRes.headers.get("set-cookie") || "";
  const cookie = setCookie.split(";")[0];

  const crumbRes = await fetch("https://query2.finance.yahoo.com/v1/test/getcrumb", {
    headers: { "User-Agent": "Mozilla/5.0", "Cookie": cookie }
  });
  const crumb = await crumbRes.text();

  if (!crumb || crumb.includes("<html")) {
    throw new Error("Failed to obtain Yahoo crumb token");
  }

  cachedCrumb = crumb;
  cachedCookie = cookie;
  return { crumb, cookie };
}

async function fetchLivePrice(symbol) {
  const { crumb, cookie } = await getCrumbAndCookie();
  const yahooSymbol = toYahooSymbol(symbol);

  const url = `https://query2.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yahooSymbol)}` +
              `?interval=1m&crumb=${encodeURIComponent(crumb)}`;

  const res = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0", "Cookie": cookie }
  });

  if (!res.ok) throw new Error(`Yahoo returned HTTP ${res.status} for ${yahooSymbol}`);

  const data = await res.json();
  const meta = data?.chart?.result?.[0]?.meta;
  const price = meta?.regularMarketPrice;
  const previousClose = meta?.chartPreviousClose ?? meta?.previousClose ?? null;

  if (typeof price !== "number" || price <= 0) {
    throw new Error(`No valid price in response for ${yahooSymbol}`);
  }

  return { price, previousClose: typeof previousClose === "number" ? previousClose : null };
}

async function updateAllWatchlistPrices() {
  // Same collectionGroup approach as updateAllPrices() — watchlist docs
  // live under users/{uid}/watchlist and there's no guaranteed parent doc.
  const watchlistSnap = await db.collectionGroup("watchlist").get();

  if (watchlistSnap.empty) {
    console.log("No watchlist stocks — nothing to update.");
    return;
  }

  const lookup = loadIndustryLookup();
  const bySymbol = new Map(); // symbol -> [{uid, docId, hasIndustry}]

  watchlistSnap.forEach((wlDoc) => {
    const uid = wlDoc.ref.parent.parent?.id;
    if (!uid) {
      console.warn(`Skipping ${wlDoc.ref.path} — not under users/{uid}/watchlist`);
      return;
    }
    const data = wlDoc.data();
    const symbol = data.symbol || wlDoc.id;
    const hasIndustry = Boolean(data.industryGroup && data.industry);
    if (!bySymbol.has(symbol)) bySymbol.set(symbol, []);
    bySymbol.get(symbol).push({ uid, docId: wlDoc.id, hasIndustry });
  });

  let updated = 0;
  let failed = 0;
  const batch = db.batch();

  for (const [symbol, refs] of bySymbol.entries()) {
    const { industryGroup, industry } = lookupIndustry(lookup, symbol);

    try {
      const { price, previousClose } = await fetchLivePrice(symbol);
      const change = typeof previousClose === "number" && previousClose > 0 ? price - previousClose : null;
      const changePercent = change !== null ? (change / previousClose) * 100 : null;

      refs.forEach(({ uid, docId, hasIndustry }) => {
        const ref = db.collection("users").doc(uid).collection("watchlist").doc(docId);
        const update = {
          currentPrice: price,
          previousClose: previousClose,
          change: change,
          changePercent: changePercent
        };
        // Only fill in industry fields if they're missing/blank — never
        // clobber a value the front-end already wrote at star-click time.
        if (!hasIndustry) {
          update.industryGroup = industryGroup || "";
          update.industry = industry || "";
        }
        batch.update(ref, update);
      });
      updated += refs.length;
      console.log(`✓ [watchlist] ${symbol}: ${price}`);
    } catch (err) {
      console.warn(`✗ [watchlist] ${symbol}: ${err.message}`);
      failed += refs.length;
    }
  }

  await batch.commit();
  console.log(`Watchlist done. updated=${updated} failed=${failed}`);
}

async function updateAllPrices() {
  // IMPORTANT: positions live under users/{uid}/positions, but the app
  // never explicitly creates a users/{uid} parent document — it only ever
  // writes into the subcollection. Firestore won't list a parent doc in a
  // plain collection("users").get() query unless that doc itself was
  // written at some point, so we use a collectionGroup query instead,
  // which finds every "positions" subcollection across all users
  // regardless of whether their parent doc exists.
  const positionsSnap = await db.collectionGroup("positions").get();

  if (positionsSnap.empty) {
    console.log("No open positions — nothing to update.");
    return;
  }

  const bySymbol = new Map(); // symbol -> [{uid, docId}]

  positionsSnap.forEach((posDoc) => {
    // Skip anything that isn't actually under users/{uid}/positions —
    // e.g. leftover docs in an old top-level "positions" collection from
    // a previous version of this app. Those have no grandparent, so
    // parent.parent is null instead of a uid.
    const uid = posDoc.ref.parent.parent?.id;
    if (!uid) {
      console.warn(`Skipping ${posDoc.ref.path} — not under users/{uid}/positions`);
      return;
    }

    const symbol = posDoc.data().symbol;
    if (!bySymbol.has(symbol)) bySymbol.set(symbol, []);
    bySymbol.get(symbol).push({ uid, docId: posDoc.id });
  });

  let updated = 0;
  let failed = 0;
  const batch = db.batch();

  for (const [symbol, refs] of bySymbol.entries()) {
    try {
      const { price } = await fetchLivePrice(symbol);
      refs.forEach(({ uid, docId }) => {
        const ref = db.collection("users").doc(uid).collection("positions").doc(docId);
        batch.update(ref, { currentPrice: price });
      });
      updated += refs.length;
      console.log(`✓ ${symbol}: ${price}`);
    } catch (err) {
      console.warn(`✗ ${symbol}: ${err.message}`);
      failed += refs.length;
    }
  }

  await batch.commit();
  console.log(`Done. updated=${updated} failed=${failed}`);
}

updateAllPrices()
  .then(() => updateAllWatchlistPrices())
  .then(() => process.exit(0))
  .catch((err) => {
    console.error("Fatal error:", err);
    process.exit(1);
  });
