# Extraction prompt — DAE National Agrometeorological Advisory Bulletin

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/DAE_Agromet_Advisory_Bulletin.pdf` (10 pages, English, text-based)
- **Org:** Agro-Meteorological Information Systems Development Project, Department of
  Agricultural Extension (DAE), Ministry of Agriculture
- **Save output to:** `backend/data/kb/agromet_advisory.md`

## Why this doc is special
It links **weather conditions → specific farm actions**. That's gold for weather-triggered
advice. Extract the decision logic, not just prose.

## What to extract
- `## Weather-to-action rules` — every "if weather then do X" advisory you can find, as
  bullet rules. Examples of the shape (use the bulletin's ACTUAL thresholds/values, not these):
  - "If heavy rainfall forecast within N days → delay top-dressing of urea to reduce runoff loss."
  - "If temperature above X°C at flowering → give supplemental irrigation."
  - "If dry spell → mulch / irrigate at critical stage."
- One `## <Crop> advisory` section per crop the bulletin gives stage-specific advice for
  (rice, maize, vegetables, etc.): current-stage actions tied to the forecast.
- `## Standard weather thresholds` — any numeric thresholds the bulletin uses (rainfall mm,
  temperature °C, humidity %) that trigger advisories.

Keep all numbers and day-counts exactly. Cite page numbers.
