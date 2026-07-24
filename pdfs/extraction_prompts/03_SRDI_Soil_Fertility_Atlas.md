# Extraction prompt — SRDI Soil Fertility Atlas Bangladesh 2020

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/SRDI_Soil_Fertility_Atlas_2020.pdf` (20 pages, English, text-based)
- **Org:** Soil Resource Development Institute (SRDI), Ministry of Agriculture, 2020
- **Save output to:** `backend/data/kb/soil_fertility_atlas.md`

## What to extract
This atlas maps soil fertility/nutrient status across Bangladesh. Create sections:

- `## Soil texture and types in Bangladesh` — the main soil texture classes and where they
  occur (region/AEZ names), and which crops each texture suits. Keep it practical.
- One `## <Nutrient> status` section for each nutrient the atlas covers
  (Organic matter, Nitrogen, Phosphorus, Potassium, Sulphur, Zinc, Boron): which
  regions/AEZs are Low / Medium / High, and what that means for fertilizer need.
- `## Soil pH` — acidic vs alkaline regions and the crops/amendments affected.
- `## Agro-Ecological Zones (AEZ) quick reference` — if the atlas lists AEZs, give a short
  bullet list of the major ones and their dominant soil character.

Cite page numbers. Keep every classification (Low/Medium/High) exactly as printed.
Do not reproduce map images; describe the data in text.
