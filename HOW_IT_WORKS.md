# AgriSense — How It Works (judge-facing explainer)

## In one line
An **AI agent** that takes a Bangladeshi farmer from an empty field to a **costed, weather-aware season plan** — and keeps advising through harvest. It talks to the farmer, pulls **real data**, does the **math in Python**, and shows a **live trace** so every number is verifiable.

---

## Tech stack (what we used and why)
| Layer | Tech | Why |
|---|---|---|
| Agent brain | **OpenAI `gpt-5.1`** (tool-calling) | decides which tools to call, chains steps |
| Backend | **Python + FastAPI + Uvicorn** | serves the API and streams the trace |
| Knowledge base (RAG) | **ChromaDB** (embedded vector DB) | search real agronomy docs |
| Memory | **SQLite** | remembers the farm across sessions |
| Frontend | **plain HTML/CSS/JS** (no framework) | fast, simple chat + trace UI |
| Weather | **Open-Meteo** (free, live API) | real rainfall/temperature |
| Payments | **bdapps TAP CaaS API** (real sandbox) | charge mobile balance + SMS |
| Web fallback | **DuckDuckGo (ddgs, no key)** | look up facts not in the KB |
| Maps | **rasterio** (offline bake only) | soil + AWD maps → small JSON |

---

## The big idea: it's an AGENT, not a chatbot
A chatbot answers one question. Our agent, for **one** farmer message, **chains many tool calls** toward a goal, remembers context, and adapts. Example: *"2 acres in Bogura, 80k budget"* triggers **8+ tool calls** in one turn (location → soil → weather → knowledge → 3× finance…). You can watch all of it in the right-hand **trace panel** — that's the proof nothing is made up.

---

## How one request flows
1. Farmer types a message → **FastAPI** `/api/chat`.
2. **`loop.py`** (the agent loop): saves the message to SQLite, loads the farm profile + history, builds the system prompt, and calls OpenAI with all the tools.
3. OpenAI decides which tools to call → **`tools.py` dispatch** runs them → results go back to the model → it may call more tools (up to 10 steps).
4. Every step is **streamed to the UI as NDJSON**: `tool_call`, `tool_result`, `final` → chat on the left, live trace on the right.

---

## The tools (21) — what each does
**Grounding / real data**
- `geocode_location` — place name → GPS (Open-Meteo, live)
- `get_weather_forecast` — real rainfall/temp (Open-Meteo, live)
- `lookup_soil_texture` — GPS → soil type, from the **real SRDI soil map** (auto-detects soil so we don't have to ask)
- `lookup_awd_suitability` — GPS → is water-saving **AWD** rice irrigation suitable here (real BRRI/IRRI map, ~25-30% irrigation saving)
- `search_knowledge_base` — **RAG** over 19 real gov docs (fertilizer guide, rice guide, soil, pest, yields, **DAM market prices**)
- `web_search` — last-resort web lookup for anything not in the KB; **saves the result back into the KB** (labeled "unverified")

**The math (deterministic Python — never the LLM)**
- `compute_financials` — crop cost breakdown, yield, revenue, net profit, ROI, break-even
- `generate_season_plan` — a **dated, validated** calendar (land prep → fertilizer splits → irrigation → pest checks → harvest)
- `assess_pest_risk` — likely pests/diseases from weather + growth stage, with treatment + cost
- `market_price_intelligence` — **sell now / store / wait** using real DAM price trend + storage/spoilage math
- `compute_livestock_financials` / `generate_livestock_plan` — same rigor for animals (broiler, goat, cattle, dairy) + vaccination calendar

**Prices & buying**
- `get_market_prices` — what the farmer SELLS (crop prices; real DAM + seeded fallback)
- `get_input_prices` — what the farmer BUYS (fertilizer/seed/pesticide/livestock feed & vaccine)
- `compare_suppliers` — rank dealers by price/delivery/distance/rating

**Vision & contact**
- `diagnose_leaf` (vision) — the farmer uploads/snaps a leaf photo → the vision model (gpt-4o-mini) identifies the disease/pest, then the agent grounds the treatment against the pest KB. Labeled "AI visual assessment — confirm with DAE".
- **Tap-to-dial an officer** — when the farmer wants to call a কৃষি কর্মকর্তা, the agent gives the real **Krishi Call Center 16123** + web-searches the local DAE office number, as a one-tap phone-dialer button (`[[CALL]]` token).

**Actions & memory**
- `save_farm_profile` — persist the farm to SQLite (memory across sessions)
- `clear_farm_data` — "forget me" (confirm-gated) — privacy
- `check_weather_alerts` — proactive: heavy rain near a fertilizer date → delay it (shows as a banner, no chat turn needed)
- `bdapps_query_balance` / `bdapps_send_sms` / `bdapps_checkout` — **real mobile payment**: charge the balance + send an SMS receipt

---

## Data files (where the "knowledge" lives)
- `data/kb/` — **19 documents** the RAG searches (real gov sources + DAM prices)
- `crops.json`, `livestock.json`, `pests.json`, `suppliers.json`, `input_prices.json`, `market_prices.json`, `price_seasonality.json` — seeded reference numbers (clearly labeled)
- `soil_grid.json`, `awd_grid.json` — the real maps, baked to small JSON so lookups are instant with no heavy dependency

---

## 📚 Data sources & the agencies behind them (full forms)
All the agronomy knowledge is compiled from **publicly available Bangladesh government & research sources** — each KB file cites its source. If a judge asks "where did this come from?", this is the answer:

| Agency (full form) | What it is | What we use from it |
|---|---|---|
| **BARC** — Bangladesh Agricultural Research Council | apex agri-research coordinator | **FRG 2024** (Fertilizer Recommendation Guide) → per-crop fertilizer doses (`frg_fertilizer_2024.md`) |
| **BRRI** — Bangladesh Rice Research Institute | national rice institute | *Modern Rice Cultivation* (আধুনিক ধানের চাষ) → rice varieties, seedbed, water, pests (`rice_cultivation.md`); + AWD suitability maps |
| **SRDI** — Soil Resource Development Institute | national soil survey body | *Soil Fertility Atlas 2020* + soil-texture rasters (clay/sand/silt) → soil auto-detect (`soil_fertility_atlas.md`, `soil_grid.json`) |
| **DAE** — Department of Agricultural Extension | farmer-extension wing | Agromet advisory (weather→action) + Plant Protection/IPM (`agromet_advisory.md`, `plant_protection.md`) |
| **DAM** — Department of Agricultural Marketing | official market-price authority | 8 division-wise retail price reports — today / last-month / last-year (`dam_prices_*.md`) |
| **BBS** — Bangladesh Bureau of Statistics | national statistics office | *Yearbook of Agricultural Statistics 2024* → real yield baselines (`crop_yield_stats.md`) |
| **DLS** — Department of Livestock Services | national livestock authority | livestock feeding / vaccination / disease guide (`livestock_guide.md`) |
| **BLRI** — Bangladesh Livestock Research Institute | livestock research institute | livestock rearing guidance (with DLS) |
| **IRRI** — International Rice Research Institute | global rice research (Philippines) | **AWD** (Alternate Wetting & Drying) suitability maps, with BRRI (`awd_grid.json`) |
| **BADC** — Bangladesh Agricultural Development Corporation | seed/input supply body | indicative input & seed dealer prices (`input_prices.json`) |

**Non-government sources:** **Open-Meteo** (free live weather + geocoding API) · **bdapps** (Robi/Axiata mobile-payment platform — real sandbox) · **DuckDuckGo** (web-search fallback, no key).

**Other abbreviations:** **FRG** = Fertilizer Recommendation Guide · **AWD** = Alternate Wetting & Drying · **IPM** = Integrated Pest Management · **RAG** = Retrieval-Augmented Generation · **CaaS** = Charging-as-a-Service · **TAP** = Telco Application Proxy (the bdapps API) · **USDA** = US Dept of Agriculture (soil-texture triangle) · **AEZ** = Agro-Ecological Zone.

---

## Real vs mock (be upfront — judges love this)
- **REAL:** weather, geocoding, RAG knowledge base, soil map, AWD map, bdapps payment (real sandbox `S1000`), web search, DAM market prices, vision leaf diagnosis.
- **SEEDED (labeled):** baseline per-acre crop costs/yields and a few input prices — compiled from the public extension sources above, used by the deterministic math.
- Full table is in the README.

---

## Why the design is trustworthy
- **All money math is Python, not the LLM** → inspectable, consistent, 67 tests.
- **Every number is traceable** in the live trace panel.
- **The LLM never invents prices/doses** — it must call a tool; if data's missing it says so (or web-searches, labeled).
- **Memory** persists in SQLite (refresh the page → the farm is still there).

---

## One-sentence answers to keep ready
- *"What's your stack?"* → FastAPI + OpenAI gpt-5.1 agent, ChromaDB RAG, SQLite memory, vanilla-JS UI; real Open-Meteo weather and real bdapps payment.
- *"Is it an agent?"* → Yes — one message triggers a chain of dependent tool calls, visible in the trace; it recovers missing info and remembers across sessions.
- *"Is this number real?"* → Point at the trace: it came from `compute_financials` / the live weather call / the DAM report — not the model.
- *"What's real vs mock?"* → Weather, RAG, maps, bdapps, prices (DAM) are real; baseline costs are seeded and labeled.
