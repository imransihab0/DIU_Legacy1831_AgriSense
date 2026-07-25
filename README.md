# AgriSense AI — Team DIU_Legacy1831

**Bdapps presents Agentic AI Hackathon (IUT 12th ICT Fest) — Final Round submission.**

An autonomous agricultural advisor that takes a farmer from an empty field to a **costed, weather-aware season plan** — and keeps advising through harvest. It converses to learn the farm, pulls **live weather**, retrieves grounded agronomy from a **RAG knowledge base**, runs all money math through a **deterministic financial engine**, remembers the farm **across sessions**, and exposes a **live agent trace** so every number can be verified against a real tool call.

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env        # then put your API key(s) in ../.env
python -m app.rag.ingest          # build the knowledge base (ChromaDB)
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** — chat on the left, live agent trace on the right.

The agent LLM is OpenAI `gpt-5.1` (model switchable live from the UI); set `OPENAI_API_KEY` in `.env`.

## Architecture

```
Farmer ⇄ Web UI (chat + live trace panel)
              │ ndjson stream
        FastAPI backend
              │
        Agent loop (OpenAI tool-calling, ≤10 steps/turn)
   ┌──────────┼─────────────┬──────────────┬─────────────┬────────────┐
 geocode  get_weather   search_kb      compute_     get_market_   bdapps_
 (live)   (live,        (RAG over      financials   prices        checkout
 Open-    Open-Meteo)   ChromaDB)      (determin-   (seeded,      (sandbox
 Meteo)                                istic Python) labeled mock) simulation)
                              │
                    save_farm_profile → SQLite (persistent memory across sessions)
```

## Tier coverage (per the problem statement)

| # | Tier 0 capability | Where |
|---|---|---|
| 1 | Conversational intake + targeted follow-ups | System prompt intake protocol; `save_farm_profile` persists each field |
| 2 | Live weather grounding | `geocode_location` + `get_weather_forecast` → **Open-Meteo (real API, no mock)** |
| 3 | Crop recommendation (≥3, ranked) | Agent workflow step 4: RAG suitability + per-crop `compute_financials` |
| 4 | Season plan (dated calendar) | **`generate_season_plan`** — deterministic, self-validating dated calendar (land prep→sowing→fertilizer splits→irrigation→pest checkpoints→harvest); doses layered from KB, dates adjusted to live forecast |
| 5 | Financial projection | `compute_financials` — deterministic Python; itemized costs, yield, revenue, net, ROI, break-even; changes correctly with inputs |
| 6 | Explained reasoning | Grounding rules force every recommendation to state its inputs |
| 7 | Knowledge base with RAG | ChromaDB over `backend/data/kb/` (BARC FRG, DAE/BRRI-derived docs) |
| 8 | Visible agent trace | Right-hand panel streams every tool call: name, params, raw result, latency |

**Tier 1:**
- **Persistent Memory:** SQLite database survives restarts and remembers farm profiles.
- **Scenario Simulation:** Re-run financials with updated `yield_factor`, `cost_factor`, or `price_factor`.
- **Fertilizer Scheduler:** Deterministic dated splits from `generate_season_plan` with doses from the KB.
- **Pest & Disease Risk:** `assess_pest_risk` combines live weather + growth stage to predict risk level, treatments, and costs.
- **Proactive Weather Alerts:** Automated UI banner polls `/api/alerts`. Heavy rain near a urea/sowing date triggers a delay warning; rain near irrigation triggers a skip warning.

**Livestock (beyond crops):**
- Animals get full parity via `compute_livestock_financials` (broiler/layer/goat/beef/dairy: cost, revenue, net, ROI, break-even).
- `generate_livestock_plan` creates dated procurement→vaccination→sale calendars grounded in a DLS/BLRI livestock KB document.

**Tier 2:**
- **Vision Diagnosis (`gpt-4o-mini`):** Analyzes leaf/crop photos to diagnose diseases and recommend treatments (auto-opens the camera/file picker; treatment grounded against the pest KB).
- **Tap-to-dial an officer:** the farmer can ask to call their local কৃষি কর্মকর্তা — the agent gives the real **Krishi Call Center 16123** and web-searches the local DAE office number as one-tap phone-dialer buttons.
- **Market Price Intelligence:** `market_price_intelligence` provides current + modeled 12-month seasonal history and deterministic sell/store/wait recommendations.
- **Supplier Comparison:** `compare_suppliers` ranks seeded dealer catalogs by price, delivery, distance, and rating.
- **bdapps CaaS Payment:** Complete TAP checkout flow (`caas/queryBalance` → `caas/directDebit` → `sms/send` receipt) built to official API specs. Real sandbox calls when credentials are provided, schema-identical labeled simulation otherwise. Bengali interaction supported natively.

## Real vs mock (required disclosure)

| Component | Status |
|---|---|
| Weather + geocoding (Open-Meteo) | **REAL** — live API calls, visible in trace |
| LLM (OpenAI gpt-5.1) | **REAL** |
| Vision LLM (OpenAI gpt-4o-mini) | **REAL** — processes uploaded crop photos for disease diagnosis |
| Knowledge base content | **REAL public sources** — 19 docs: BARC **FRG 2024** fertilizer guide, **BRRI Modern Rice Cultivation**, SRDI **Soil Fertility Atlas 2020**, DAE agromet advisory & plant protection, BBS 2024 yield stats, a DLS/BLRI livestock guide, and **8 division-wise DAM market-price reports** (see `backend/data/kb/`, each file cites its source) |
| RAG retrieval (ChromaDB) | **REAL** — actual vector search, chunks + sources visible in trace |
| Financial math | **REAL computation** — deterministic Python; baseline per-acre costs/yields are **seeded reference data** compiled from public extension sources (`backend/data/crops.json`) |
| Market (crop output) prices | **REAL (DAM) + seeded fallback** — 8 division-wise DAM retail price reports (dated current + last-month + last-year prices with % change) are in the RAG KB (`kb/dam_prices_*.md`) and the agent quotes them via search_knowledge_base; the small seeded catalog (`market_prices.json`) is a quick fallback |
| Farm input prices (fertilizer/seed/pesticide) | **SEEDED reference** — labeled catalog (`backend/data/input_prices.json`), indicative of BADC/DAE dealer rates; powers the input cart + checkout |
| bdapps CaaS payment | **Dual mode** — with `BDAPPS_APP_ID`/`BDAPPS_PASSWORD` set: **REAL sandbox HTTP calls** to `developer.bdapps.com` (`/caas/direct/debit`, `/sms/send`); without: **labeled simulation** with byte-identical request/response schemas. **Verified against the live sandbox (app DIUAIH): real `S1000` SMS and a real `S1000` direct-debit charge.** Number masking handled via auto-captured masked `subscriberId`; `paymentInstrumentName` is `"Mobile Account"`; `balance/query` + `list/pi` are not deployed on the gateway so the flow skips them gracefully. The sandbox test wallet is fixed/non-rechargeable (returns `E1378`/`E1329` once spent or over its cap); when that happens the checkout still makes the **real** debit call (in the trace) and issues the **real** receipt SMS, marking `live_deduction: false` — so every confirmed buy sends a receipt, honestly labeled as sandbox. Full flow visible in trace either way |
| Soil texture (by location) | **REAL geospatial** — SRDI soil-texture rasters (clay/sand/silt %) sampled at the farm's coordinates → USDA texture class → soil_type. Baked to a compact JSON (`lookup_soil_texture`); the agent auto-detects soil from location instead of asking |
| AWD irrigation suitability (by location) | **REAL geospatial** — BRRI/IRRI AWD suitability rasters (Boro/Aman/Aus), reprojected from UTM to a baked lat/lon JSON (`lookup_awd_suitability`); tells a rice farmer if water-saving AWD suits their field (~25-30% irrigation saving) |
| Season-plan dates | **REAL computation** — deterministic Python calendar with validation (`generate_season_plan`); stage schedule from standard agronomic practice |
| Livestock cost/yield baselines | **SEEDED reference** — labeled catalog (`backend/data/livestock.json`), from DLS/BLRI extension guidance; deterministic engine |
| Web-search fallback | **REAL external search** (DuckDuckGo, no key) — only when the KB/catalogs have no answer; results are labeled **`web (unverified)`**, appended to the RAG KB (kept separate from vetted gov docs), and retrievable next time without re-searching. Agent always presents them as web-sourced/unverified |
| Farm memory (SQLite) | **REAL** — persists across sessions |

## Tools & APIs used

- **OpenAI API** (`gpt-5.1`) — the agent LLM (model switchable live from the UI)
- **Open-Meteo** forecast + geocoding — free, live, no key
- **ChromaDB** (embedded) — vector store for RAG
- **FastAPI + Uvicorn** — backend; **SQLite** — memory; vanilla JS — frontend
- Built during the event with **Claude Code** and **Codex** as pair-programmers (allowed per rules)

## Demo script (4 min)

1. "I have 2 acres in Bogura, budget 80k" → agent asks only the missing fields (soil, water, season).
2. Watch the trace: geocode → live 14-day forecast → RAG lookups → 3 crop rankings each with financials → recommendation with stated reasons.
3. Pick a crop → dated calendar (land prep → fertilizer splits → irrigation → pest checkpoints → harvest) + full financial projection.
4. "What if my budget is cut 40%?" → re-ran financials, changed numbers side-by-side.
5. Buy seed → bdapps sandbox checkout, request/response + receipt in the trace.
6. Refresh the page mid-demo → the agent still remembers the farm (persistent memory).
