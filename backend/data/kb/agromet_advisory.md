<!-- SOURCE: National Agrometeorological Advisory Service Bulletin | Agro-Meteorological Information Systems Development Project, Department of Agricultural Extension (DAE), Ministry of Agriculture, with Bangladesh Meteorological Department | 2023 | official gov publication | REAL public source -->
# DAE National Agromet Advisory — Weather-to-Action Rules

<!-- NOTE: this bulletin issues national + 64-district advisories tying the
forecast to specific farm actions. Rules below are the decision logic to reuse
in the weather-triggered advice module; thresholds/actions are copied from the
15-22 March 2023 bulletin. The agent should pair these rules with its LIVE
Open-Meteo forecast for the farm's district. -->

## Weather-to-action rules (heavy rain / thunderstorm forecast)
From the Agromet Advisories section (p.10), issued when light-to-heavy rainfall
+ possible thunderstorms are forecast across districts:
- **If heavy rainfall/thunderstorms forecast → avoid irrigation, fertilizer, and pesticide application** (they wash off / are wasted). This is the core weather-trigger rule: delay top-dressing urea before rain to cut runoff loss.
- **Harvest mature crops quickly** and store in a dry, safe place before the rain.
- **Keep drains clear** so water does not accumulate on the field.
- **Arrange raised/elevated bunding** around and inside Boro paddy plots to hold or drain water as needed.
- **Provide mechanical support (staking)** to standing banana, sugarcane, and other tall/horticultural crops against gusty/squally wind.

## Boro rice — weather-linked disease action (p.10)
- **Bacterial leaf blight (BLB) risk rises with rain in Boro rice.**
- Preventive after rain stops: apply **5 kg potash (MoP) + 3.5 kg gypsum per bigha**.
- If the crop has passed the **panicle initiation (PI) stage**: mix **60 g potash + 60 g Thiovit + 20 g zinc in 10 litres water** and spray over 5% of the land (i.e., spot/rate basis as printed).
- Rule of thumb encoded: rain + Boro at/after PI → BLB watch + the potash/gypsum or spray remedy above.

## Standard weather parameters the bulletin tracks
- **Bright sunshine hours**: ~6.78 hr/day (last week); forecast range 5.50–7.50 hr/day.
- **Free water loss (evaporation proxy)**: ~3.57 mm/day (last week); forecast 2.50–4.50 mm/day. High free-water-loss + dry spell → irrigation need rises at critical stages.
- **Rainfall (last 24 h), max temp (previous day), min temp (current day)** are reported per location; **district-wise quantitative 5-day forecast** is published each issue.
- Satellite products used: NDVI (vegetation greenness), VCI, TCI, VHI (vegetation/temperature/health condition indices) — proxies for crop stress by region.

## How the agent should use this
- Bulletin is issued for a fixed 5–7 day window per district; treat its RULES as durable and plug in the farm's **live forecast** (Open-Meteo) for actual numbers.
- The central, reusable trigger: **rain in the next few days ⇒ postpone urea top-dressing / fertilizer / pesticide, secure drainage, stake tall crops, and raise disease watch (BLB in rice).** This is exactly the Tier-1 "proactive weather-triggered advice" behavior.
- Disclaimer in source: these district bulletins are experimental and published via the DAE website for feedback (p.1).
