# AgriSense — Booth Demo Playbook (judges come to you)

## ⏱️ Before judges arrive (setup checklist)
- [ ] `cd backend && source .venv/bin/activate && python -m app.rag.ingest` → should say **~195 chunks / 19 docs**
- [ ] `uvicorn app.main:app --port 8000` running; open **http://localhost:8000**
- [ ] `.env` has OpenAI key + bdapps creds (`APP_139267`) → bdapps runs REAL
- [ ] Phone `8801875191553` handy (receipt SMS lands there — show the judge the real SMS!)
- [ ] Click **"New farm"** to start clean; internet on (weather + web-search are live)

## 🎤 30-second opener (when a judge sits down)
> "AgriSense takes a farmer from an empty field to a costed, weather-aware season plan — and it's a real **agent**, not a chatbot. Everything on the right is a **live trace**: every number you'll see came from a real tool call, not the model's imagination. Let me show you."

## ▶️ The 4-minute run (do it in this order)
1. **Vague intake** — type: *"আমার ২ একর জমি বগুড়ায়, বাজেট ৮০ হাজার, বোরো মৌসুম। কী চাষ করব?"*
   → Point at trace: **geocode → lookup_soil_texture (auto-detects soil from the real SRDI map!) → live weather → RAG → compute_financials ×3**.
   → Say: *"It asked nothing extra — it detected the soil from the location and scaled to the budget."*
2. **3 crops, costed** — it ranks 3 crops with cost/profit/ROI. → *"Change the budget and the numbers change — the math is a deterministic Python engine, not the LLM."*
3. **Pick a crop → dated plan** — *"বোরো ধানের সম্পূর্ণ প্ল্যান দাও"* → dated calendar (land prep→fertilizer splits→harvest), **deterministic + validated**.
4. **AWD wow** — *"সেচের খরচ কমানোর উপায়?"* → real BRRI/IRRI map → *"your area is suitable for AWD → save ~25-30% irrigation cost."*
5. **Proactive alert** — point at the **weather alert banner** (updates with no chat turn).
6. **bdapps LIVE** — buy an input via the 🛒 order dialog → confirm → **show the real receipt SMS on your phone** + `S1000` in the trace.
7. **Memory** — hit **refresh** → farm still remembered.

## 🛡️ Q&A — likely questions & sharp answers (trace = proof)
| Judge asks | Your answer |
|---|---|
| "Is the weather real or faked?" | **Real** — Open-Meteo live API. Point at the raw response in the trace; refresh to show it changes. |
| "Did the AI make up this profit number?" | **No** — point at `compute_financials` in the trace: itemized costs → net/ROI. Deterministic Python, 65 tests. |
| "What's your RAG / knowledge base?" | **19 real gov docs / 195 chunks** — BARC FRG 2024, BRRI rice, SRDI soil, DAE pest, BBS yields, **8 DAM price reports**. Show a `search_knowledge_base` hit in the trace with the source name. |
| "Are the market prices real?" | **Real DAM division reports** (dated, with month/year trend) via RAG + a small seeded fallback (labeled). |
| "What if you ask something not in the KB?" | It **web-searches**, labels the result **"web (unverified)"**, and **saves it to the KB** for next time. Demo with an odd crop (e.g. mushroom/broccoli price). |
| "Real vs mock?" | README has a full table. Real: weather, RAG, soil map, AWD map, bdapps sandbox. Seeded (labeled): baseline crop costs, a few input prices. |
| "Is bdapps really working?" | **Yes, real sandbox** — got a real `S1000` charge + SMS. Show the receipt on the phone. (Test wallet is capped/empty by design, so it labels `[on test]`.) |
| "Show me it's an agent not a chatbot." | One message → 6+ chained tool calls in the trace; it recovers missing info (auto soil), remembers across refresh, adapts to weather. |
| "Does it handle Bengali?" | Whole demo is in Bengali. Farmer can also use voice-free tap chips. |
| "Privacy?" | Farmer can say "আমার তথ্য মুছে ফেলো" → confirm → data wiped. bdapps passwords redacted, numbers masked, `.env` never committed. |
| "What if the network dies?" | Weather has a labeled cached fallback; tools fail gracefully, no crash. |

## 🎯 Point-scoring lines to drop
- **Agentic (20):** "one request → a chain of dependent tool calls, visible in the trace."
- **Accuracy (20):** "every number is traceable to a real tool; the finance is deterministic Python."
- **KB (12):** "19 real gov sources, and it fills its own gaps via web search."
- **bdapps (10):** show the real receipt SMS.
- **Innovation (5):** soil auto-detect + AWD map + proactive alerts + self-updating KB + livestock parity.

## ⚠️ If something breaks live
- Weather/geo slow → keep talking; it caches. bdapps balance empty → that's expected sandbox behavior (`[on test]`), the flow + SMS still prove it.
- Web search flaky → the price may already be cached in the KB; move on.
- Always fall back to: **"look at the trace — that's the real tool call."**
