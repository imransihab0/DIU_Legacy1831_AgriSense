# Extraction prompt — BBS Yearbook of Agricultural Statistics 2024

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/BBS_Agri_Statistics_Yearbook_2024.pdf` (696 pages, English tables)
- **Org:** Bangladesh Bureau of Statistics (BBS), 36th Series, June 2025
- **Save output to:** `backend/data/kb/crop_yield_stats.md`

## Purpose
Give the agent **real yield baselines** (production ÷ area) to sanity-check profit
estimates. This PDF is huge — extract ONLY summary/national + divisional figures, NOT the
per-district tables.

## What to extract
For each crop below, find the **Area and Production** table (latest year available, e.g.
2023-24). Create one `## <Crop> — area, production, yield` section with:
- **National** total Area (acre or hectare — keep unit) and Production (M.Ton) for the
  latest year.
- **Divisional** breakdown (8 divisions) if easily available — one line each.
- **Computed yield** = Production ÷ Area, stated in **ton/acre** (or ton/ha), so the number
  is directly usable. Show the arithmetic once, e.g. "yield = 5.2M ton ÷ 4.1M acre ≈ 1.27 ton/acre".
- Cite the table number and page.

## Crops to cover
Boro rice, Aman rice, Aus rice, Wheat, Maize, Potato, Onion, Mustard, Lentil, Jute.

Round computed yields to 2 decimals but keep the source Area/Production numbers exact.
Do NOT transcribe district-level rows.
