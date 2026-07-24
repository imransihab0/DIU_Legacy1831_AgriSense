# Extraction prompt — Bangladesh Plant Protection Country Report

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/Bangladesh_Plant_Protection_Report_2015.pdf` (32 pages, English, text-based)
- **Org:** Plant Protection Wing, Department of Agricultural Extension (DAE) — Country Report, 2015
- **Save output to:** `backend/data/kb/plant_protection.md`

## What to extract
Pest & disease management knowledge. Create:

- One `## <Crop> — pests & diseases` section per major crop discussed (rice, wheat, maize,
  potato, vegetables, pulses, jute): the key pests/diseases named, their symptoms, the
  growth stage they hit, and the recommended **IPM / preventive** and **treatment** action.
- `## IPM principles` — the report's integrated pest management approach in bullet form
  (cultural, biological, chemical-as-last-resort, etc.).
- `## Pesticide safety / regulation` — any rules on approved pesticides, safe use, banned
  chemicals mentioned.

If the report is more policy than field-level, still pull whatever crop-pest specifics
exist. Cite page numbers. Do not invent chemical names or doses — only what's printed.
