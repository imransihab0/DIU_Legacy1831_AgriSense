# PDF → Knowledge Base extraction plan

Feed each numbered prompt (with its source PDF) to a vision-capable AI. Each prompt is
self-contained but references `_SHARED_RULES.md` — give the AI **both** the shared rules and
the specific prompt, plus the PDF. The AI writes one `.md` file into `backend/data/kb/`.

After all files land in `backend/data/kb/`, come back here and run:
```bash
cd backend && source .venv/bin/activate && python -m app.rag.ingest
```
That re-chunks the whole KB into ChromaDB. Then confirm with:
```bash
curl -s localhost:8000/api/health   # kb_chunks should jump well above 31
```

## Chosen PDFs → output KB files

| Prompt | Source PDF | Output → `backend/data/kb/` | Value | Text OK? |
|---|---|---|---|---|
| 01 | `BARC_FRG_2024.pdf` | `frg_fertilizer_2024.md` | **Highest** — fertilizer doses | ✅ English text |
| 02 | `BARI_Krishi_Projukti_Hatboi.pdf` | `crop_technology.md` | High — full crop packages | ⚠️ **Bangla, needs VISION/OCR** (text layer is garbage) |
| 03 | `SRDI_Soil_Fertility_Atlas_2020.pdf` | `soil_fertility_atlas.md` | High — soil/nutrient status | ✅ English text |
| 04 | `DAE_Agromet_Advisory_Bulletin.pdf` | `agromet_advisory.md` | High — weather→action rules | ✅ English text |
| 05 | `Bangladesh_Plant_Protection_Report_2015.pdf` | `plant_protection.md` | Medium — pests/diseases | ✅ English text |
| 06 | `BBS_Agri_Statistics_Yearbook_2024.pdf` | `crop_yield_stats.md` | Medium — real yield baselines | ✅ English tables |
| 07 | `BRRI_Rice_Guide.pdf` ⏳ *(you're downloading)* | `rice_cultivation.md` | High — rice (BARI doc skips it) | ⚠️ likely Bangla, vision/OCR |
| 08 | `DAM_Market_Prices.pdf` ⏳ *(you're downloading)* | `market_prices_dam.md` | High — de-mocks prices | ✅ table |

Do **01, 03, 04** first — they're the cheapest wins (clean English text, directly grounds
fertilizer / soil / weather advice). **02** is the richest but costs the most (vision/OCR).

## Deleted (were climate-policy docs, not agronomy)
- ~~`1.Draft Final Report climate change forecasting.pdf`~~ — climate forecasting draft. DELETED.
- ~~`BGD214817.pdf`~~ — Bangladesh National Adaptation Plan (NAP) 2022, climate policy. DELETED.

- ~~`ADC.pdf`~~ — scanned, no metadata, unidentified. DELETED.

## Still to download (prompts 07 & 08 are ready and waiting)
- **BRRI rice guide** → save as `pdfs/BRRI_Rice_Guide.pdf` (brri.gov.bd). Fills the rice gap.
- **DAM market price bulletin** → save as `pdfs/DAM_Market_Prices.pdf` (dam.gov.bd, latest issue).

## The `.tif` maps (`pdfs/.tif/`) — different track, NOT for RAG
`BD_Dekadal_Rainfall.tif`, `BD_Dekadal_PET.tif`, and the `.rar` maps
(`BD_Soiltexture`, `BD_AWD_Suitability_Map`) are **geospatial rasters**, not text — RAG can't
use them. They'd power a *different* feature: a `lookup_soil_texture(lat, lon)` /
`lookup_rainfall(lat, lon)` tool that samples the raster at the farm's coordinates. That needs
`rasterio`/GDAL and is a separate build. Weather is already live via Open-Meteo, so these are
optional. Flagged here so we don't forget them — decide later.
