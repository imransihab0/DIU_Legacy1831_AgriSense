# Extraction prompt — BARC Fertilizer Recommendation Guide 2024

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/BARC_FRG_2024.pdf` (260 pages, English, text-based)
- **Org:** Bangladesh Agricultural Research Council (BARC), FRG 2024
- **Save output to:** `backend/data/kb/frg_fertilizer_2024.md`
- **This is the single most important document. Prioritize it.**

## What to extract
The per-crop **fertilizer recommendations**. For each crop below, create one
`## <Crop> — fertilizer` section containing:
- Recommended dose of each nutrient/fertilizer: **Urea, TSP, MoP, Gypsum (S), Zinc
  sulphate, Boron** (and DAP/others if the guide lists them).
- Keep the guide's unit (usually **kg/ha**; if the guide also gives kg/acre or kg/bigha,
  include it). State the unit clearly.
- **Application timing / splits** if given (e.g. "all TSP/MoP + 1/3 urea at final land
  prep; remaining urea in 2 splits at tillering and panicle initiation").
- If the guide varies the dose by **soil fertility level (High/Medium/Low)** or by **AEZ
  (Agro-Ecological Zone)**, capture the Medium/most-common level and note that it varies.
- Cite page numbers.

## Crops to cover (in this order; skip any the guide doesn't have)
Boro rice, Aman rice, Aus rice, Wheat, Maize (Bhutta), Potato (Aloo), Mustard (Sarisha),
Lentil (Masur), Onion (Piaj), Tomato, Brinjal (Begun), Jute (Pat).

## Also add (one section each, if present)
- `## How FRG doses are adjusted` — the guide's rule for adjusting by soil test / STVI /
  organic matter, in 4–6 lines.
- `## Nutrient roles quick reference` — 1 line each: what N, P, K, S, Zn, B do for the crop.

Stop after these. Do not transcribe the AEZ tables in full.
