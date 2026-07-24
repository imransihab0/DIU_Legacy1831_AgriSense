# Extraction prompt — DAM Market Price Bulletin  (⏳ awaiting PDF)

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/DAM_Market_Prices.pdf`  ← save the download here with this exact name
- **Org:** Department of Agricultural Marketing (DAM), Ministry of Agriculture, `www.dam.gov.bd`
  (daily/weekly wholesale & retail price bulletin — grab the most recent issue)
- **Save output to:** `backend/data/kb/market_prices_dam.md`
- **Why:** app prices are currently MOCK. This gives a REAL, dated, cited price source.

## ⚠️ Note the bulletin date
Put the **exact bulletin date** in the SOURCE header and at the top of the file — prices are
time-specific and must be labeled with their date so the app can say "as of <date>".

## What to extract
- `## Crop output prices` — for each commodity in the bulletin, a line:
  `<Commodity (local name)>: wholesale ৳X–Y /<unit>, retail ৳X–Y /<unit>` — keep the unit
  (per kg / per maund / per quintal) exactly as printed. Cover at least: coarse & fine rice,
  wheat, maize, potato, onion, lentil (masur), mustard, and any vegetables listed.
- `## Fertilizer / input prices` — if the bulletin lists Urea/TSP/MoP/DAP dealer prices,
  capture them (per kg or per 50kg bag), labeled.
- `## Market / location` — which market(s) or region the prices are for (Dhaka wholesale, etc.).

Copy every price range exactly; do not average. If only one number is given, use it as-is.
