# AgriSense AI — Requirements, Completion Review & Priorities

Source reviewed: `Agentic_AI_Hackathon_Final_Question.pdf` (Final Round problem statement), against the repository state on 24 July 2026.

## Status key

- **[x] Completed (code-reviewed):** implemented in the current codebase.
- **[~] Partial / demo-verify:** some implementation exists, but a required behaviour is not fully automated or has not been verified end to end.
- **[ ] Not completed:** no implementation found.

> **Current assessment:** all **8 Tier 0 capabilities are implemented in code**, and the project also implements persistent memory, scenario finance, and a bdapps payment simulation. The main risk is not missing core features; it is proving them reliably in a clean live demo and closing a few integration/quality gaps. Runtime tests could not be executed here because the Python dependencies have not been installed (`ModuleNotFoundError: dotenv`).

## Functional requirements

### Tier 0 — required core

| Status | Requirement from brief | Current evidence | Improvement / acceptance check |
|---|---|---|---|
| [x] | Collect location, farm size, soil type, water availability, budget and target season from a vague conversation; ask only for missing fields. | Intake rules in `backend/app/agent/prompts.py`; profile saved in SQLite through `save_farm_profile`. | Demo with a vague opening and confirm only missing fields are asked. Add automated intake tests. |
| [x] | Use a real weather API for the farm location; use returned rain and temperature in advice. | Open-Meteo geocoding and forecast tools in `backend/app/tools/weather.py`; tool trace exposes raw response. | Verify with network access during demo; visibly reference exact returned values. Clearly label cached fallback data as cached. |
| [x] | Rank at least 3 crops, each with suitability, water need, risk and rough profit estimate. | Agent workflow requires 3 candidates; `crops.json` and `compute_financials` provide crop attributes and profit estimates. | Run one full profile and confirm the model calls finance once per candidate and outputs all four comparison fields. |
| [x] | Produce a dated season calendar from land preparation to harvest, including sowing, fertilizer, irrigation, weed/pest checkpoints and harvest. | **Deterministic `generate_season_plan` tool** (backend/app/tools/season_plan.py) computes and self-validates the dated calendar; agent layers KB doses + forecast adjustments. 9 tests. | Done — dates no longer depend on LLM formatting. |
| [x] | Give itemized costs, expected yield, revenue, net profit, ROI and break-even; calculations must update correctly. | Deterministic `compute_financials` engine plus 8 finance tests in `backend/tests/test_finance.py`. | Install dependencies and run `python3 -m pytest tests/ -v`; add boundary/negative-input tests. |
| [x] | Explain every recommendation with farm inputs and retrieved data. | Strict grounding/explanation rules in the system prompt; tool results include source and weather values. | In demo, inspect every recommendation for specific soil, stage/date and forecast/source evidence; add response-evaluation tests. |
| [x] | Build and use a RAG knowledge base from public agronomy sources. | ChromaDB over **10 source-attributed KB docs / 91 chunks**, incl. real gov extractions: BARC **FRG 2024**, SRDI **Soil Fertility Atlas 2020**, DAE **Agromet Advisory**, DAE **Plant Protection 2015**, BBS **Ag-Stats Yearbook 2024 yields**, plus a livestock guide. Each cites org/year/page. | Verified retrieval pulls the new docs (FRG for doses, BBS for yields, agromet for weather rules). Pending: BARI Krishi Projukti Hatboi (Bangla/OCR), BRRI rice, DAM prices. |
| [x] | Expose every tool call, parameters and raw returned values in the interface. | NDJSON tool events from agent loop; right-hand trace panel in `frontend/`. | Test a full response and an error state in the browser; offer a trace export/copy button if time permits. |

### Tier 1 — differentiators

| Status | Requirement from brief | Current evidence | Improvement / acceptance check |
|---|---|---|---|
| [x] | Persistent farm/conversation memory across sessions. | SQLite `farms` and `messages` tables; session ID stored in browser local storage. | Refresh/restart the backend during demo and show the retained profile. Note that a new browser/device still creates a different session. |
| [x] | Proactive weather-triggered advice that watches forecasts and adjusts plans. | Season plan persisted to SQLite; `check_weather_alerts` + `/api/alerts` recompute alerts from the live forecast; UI banner polls every 5 min with **no chat turn**. Heavy rain near a urea/sowing date → delay; rain near irrigation → skip. 6 tests. | Done — non-chat proactive path. Optional: background cron + auto-SMS. |
| [~] | Fertilizer and irrigation scheduler with quantities, growth-stage timing, organic alternatives and cost. | KB and prompt can produce dates/doses; financial engine has broad cost items. | **High priority:** implement a deterministic structured scheduler with crop/soil/stage inputs, organic options and per-action cost totals. |
| [x] | Pest/disease risk from crop, growth stage and weather, with prevention/treatment and estimated cost. | `assess_pest_risk` (backend/app/tools/pest.py + pests.json) scores each threat from live temperature + moisture + growth stage, with prevention, treatment, suggested product and per-acre/total cost. 8 tests. | Done — deterministic weather+stage risk model. |
| [x] | Scenario simulation with changed numeric plans. | `yield_factor`, `cost_factor`, and `price_factor` rerun the financial engine; prompt describes the rainfall/budget/price flows. | Demo price, budget and rainfall scenarios; preserve a baseline plan for a true side-by-side comparison. |

### Tier 2 / bonus features

| Status | Requirement from brief | Current evidence | Improvement / acceptance check |
|---|---|---|---|
| [x] | Supplier marketplace comparison by price, delivery time, distance and rating. | `compare_suppliers` (suppliers.py + suppliers.json) ranks a seeded 6-dealer catalog by price/delivery/distance/rating. 4 tests. Brief explicitly accepts a seeded catalog. | Done. |
| [x] | Market-price intelligence with current/historical prices and sell/store/wait advice. | `market_price_intelligence` (market_intel.py + price_seasonality.json) returns current price, a modeled 12-month seasonal history, and a deterministic sell-now/store/wait recommendation using storage cost + spoilage. 6 tests. History is seeded/modeled and labeled; current price swaps to real DAM when that doc lands. | Done — labeled seeded/modeled. |
| [ ] | Leaf-image disease detection. | No upload endpoint or vision classifier found. | Low priority; add only after core reliability work. |
| [~] | bdapps CaaS checkout: complete request/response, balance deduction and receipt flow. | `backend/app/tools/bdapps.py` implements balance → debit → SMS, with a labeled schema-compatible simulation and credentials-based live mode. | **High priority for points:** test with sandbox credentials and document actual result; expose OTP registration in the tool registry/UI if number masking is required. |
| [x] | Bengali or voice interaction. | Bengali input/output is supported by prompt and UI copy. | Verify Bengali responses remain grounded; voice is not implemented, but is optional. |

## Non-functional requirements

| Status | Requirement | Current evidence | Improvement / acceptance check |
|---|---|---|---|
| [x] | Working web prototype with a usable chat and visible trace. | FastAPI app serves the vanilla-JS UI; trace and error rendering are implemented. | Run a browser smoke test on a clean setup. |
| [x] | Persistent, durable local state. | SQLite-backed profiles/messages; Chroma persistent store. | Add a simple migration/back-up policy if used beyond the hackathon. |
| [~] | Reliability and graceful external-service failure handling. | Weather has an explicitly labeled local cache fallback; tool dispatcher returns errors to the agent. | Add timeouts/retries/status messages for all external services, especially LLM and bdapps; test offline behaviour. |
| [~] | Security and privacy for farmer/payment data. | Passwords are redacted in displayed bdapps request payloads. | **High priority:** do not retain raw phone numbers unnecessarily; protect/reset SQLite data, validate session IDs and inputs, add rate limits, and never commit `.env` secrets. |
| [~] | Clear real-vs-mock disclosure. | README distinguishes real weather/RAG/compute from seeded prices and simulated bdapps mode. | Show the same disclosure in the UI/demo; distinguish cached weather from live weather. |
| [~] | Reproducible setup and dependency completeness. | README and `.env.example` exist; requirements list runtime libraries. | **High priority:** add `pytest` to `backend/requirements.txt` (or a dev requirements file), pin tested versions, and verify the documented setup from a new virtual environment. |
| [~] | Testability and regression protection. | Finance unit tests exist. | Add tests for weather cache, profile persistence, RAG ingestion/search, bdapps simulation, API endpoints, and one mocked end-to-end agent turn. |
| [~] | Practical accuracy / provenance. | KB documents name public organizations; financial baseline is seeded reference data. | Replace broad source attributions with exact source URLs, publication dates/pages, and review crop data with an agronomy expert. |
| [~] | Performance and demo stability. | Agent iteration limit and live stream are present. | Warm the RAG database, preflight API keys/network, show loading/error states, and prepare a clearly labeled cached/demo fallback. |

## Priority-ordered unfinished work

Priority follows the problem statement: make Tier 0 stable first, then high-value judging gaps, then bonus features.

1. **P0 — Verify the complete Tier 0 path in a clean environment.** Install dependencies, ingest the KB, start the app, run the finance tests, and record one complete farmer journey. This is the highest-value work because Tier 0 is required and scope/execution is worth 15 points.
2. **P0 — Make demo grounding auditable.** Confirm a real weather call, RAG retrieval, three financial calls and the trace all appear in one response. Add direct KB source links/page references and ensure responses cite them.
3. ~~**P0 — Harden the season-plan output.**~~ **DONE** — `generate_season_plan` computes & validates the dated calendar deterministically (9 tests). Livestock got the same treatment: `compute_livestock_financials` + `generate_livestock_plan` + a DLS/BLRI KB doc (12 tests). Suite now 30 tests.
4. **P1 — Test bdapps against the official sandbox and expose the full masking/OTP path.** Simulation is useful, but a successful sandbox flow earns the dedicated 10 points more credibly. If credentials are unavailable, label the simulation prominently in both README and UI.
5. **P1 — Implement true proactive weather alerts.** Add a scheduled forecast check tied to persisted plan dates, risk rules, in-app notifications and optional SMS. Current behaviour is reactive during a chat turn.
6. **P1 — Implement deterministic pest, fertilizer and irrigation decision tools.** This improves accuracy/practicality (20 points) and completes the remaining Tier 1 gaps, including treatment/input cost estimates.
7. **P1 — Expand automated tests and setup reliability.** Add `pytest` to install requirements, then cover persistence, RAG, weather fallback, bdapps simulation and API smoke tests.
8. **P2 — Add historical market intelligence and a sell/store/wait rule.** Keep all data explicitly labeled as real or seeded.
9. **P2 — Add a small seeded supplier comparison.** This can demonstrate the marketplace requirement without expanding scope too far.
10. **P3 — Add image diagnosis or voice only after the above is stable.** These are bonus features and should not threaten the core demo.

## Submission checklist

- [ ] Rename the repository to the required `TeamName AgriSense` format if it is not already named that remotely.
- [x] README covers setup, APIs, tier coverage and real-versus-mock disclosures.
- [ ] Verify README commands on a fresh environment; use `python3` consistently if `python` is unavailable.
- [ ] Rebuild the Chroma knowledge base before the final run.
- [ ] Prepare a 4-minute demonstration that visibly proves: missing-info recovery, live weather, RAG, three crop/finance comparisons, dated plan, memory, and trace.
- [ ] Make the final commit and push before the hard cutoff.
