<!-- SOURCE: Yearbook of Agricultural Statistics 2024 (36th Series) | Bangladesh Bureau of Statistics (BBS) | June 2025 | official gov publication | REAL public source -->
# BBS Yield Baselines (national, latest year 2023-24)

<!-- NOTE: national Area/Production from "Key Statistics" (p.xii) and Table
2.1.1 "Area, Yield Rate and Production 2021-22 to 2023-24" (p.41-42). Units as
printed: Area in '000 acres, Production in '000 metric tons. Computed
yield = Production ÷ Area = ton/acre (M.Ton per acre). These are NATIONAL
averages for sanity-checking a farm's expected yield in the financial model;
a good farm with HYV/hybrid + full inputs can exceed these, subsistence plots
fall below. Rounding may cause small mismatches (BBS footnote). -->

## Boro rice — area, production, yield (p.xii, Table 2.1.1 p.41)
- 2023-24: Area 12,052 '000 acres; Production 21,068 '000 M.Ton.
- Yield = 21,068 ÷ 12,052 ≈ **1.75 ton/acre** (Table 2.1.1 per-acre yield: Boro total 1,748 kg/acre; Hybrid 1,936; HYV 1,687).
- Highest-yielding rice season; hybrid Boro tops ~1.94 ton/acre.
- Trend: 20,186 (2021-22) → 20,768 (2022-23) → 21,068 (2023-24) '000 M.Ton.

## Aman rice — area, production, yield (p.xii, Table 2.1.1 p.41)
- 2023-24: Area 14,210 '000 acres; Production 16,656 '000 M.Ton.
- Yield = 16,656 ÷ 14,210 ≈ **1.17 ton/acre** (Table 2.1.1: Aman total 1,172 kg/acre; HYV 1,246; Hybrid 1,477).
- Largest rice area in the country; mostly rainfed HYV.

## Aus rice — area, production, yield (p.xii, Table 2.1.1 p.41)
- 2023-24: Area 2,557 '000 acres; Production 2,973 '000 M.Ton.
- Yield = 2,973 ÷ 2,557 ≈ **1.16 ton/acre** (Table 2.1.1: Aus total 1,162 kg/acre; Hybrid 1,511).
- Smallest and lowest-yielding rice season.

## Wheat — area, production, yield (p.xii, Table 2.1.1 p.41)
- 2023-24: Area 770 '000 acres; Production 1,171 '000 M.Ton.
- Yield = 1,171 ÷ 770 ≈ **1.52 ton/acre** (Table 2.1.1 per-acre yield 1,522 kg/acre).

## Maize — area, production, yield (p.xii, Table 2.1.1 p.41)
- 2023-24: Area 1,270 '000 acres; Production 4,876 '000 M.Ton.
- Yield = 4,876 ÷ 1,270 ≈ **3.84 ton/acre** (Table 2.1.1 ~3,718 kg/acre in 2022-23).
- Highest per-acre yield of the cereals — high-value, input-responsive crop.

## Potato — area, production, yield (p.xii)
- 2023-24: Area 1,133 '000 acres; Production 10,601 '000 M.Ton.
- Yield = 10,601 ÷ 1,133 ≈ **9.36 ton/acre**.
- Trend: 10,145 (2021-22) → 10,432 (2022-23) → 10,601 (2023-24) '000 M.Ton. Very high tonnage per acre; note market gluts depress price.

## Onion — area, production, yield (Table 2.1.1 p.42, p.xii)
- 2023-24: Area 513 '000 acres; Production 2,917 '000 M.Ton.
- Yield = 2,917 ÷ 513 ≈ **5.69 ton/acre** (Table 2.1.1 per-acre 5,681 kg/acre).
- Trend rising: 2,517 → 2,547 → 2,917 '000 M.Ton.

## Mustard (Rape & Mustard) — area, production, yield (Table 2.1.1 p.42)
- 2023-24: Area 1,144 '000 acres; Production 638 '000 M.Ton.
- Yield = 638 ÷ 1,144 ≈ **0.56 ton/acre** (Table 2.1.1 per-acre 557 kg/acre).
- Area expanding fast (817 → 947 → 1,144 '000 acres) under oilseed self-sufficiency push.

## Lentil / Pulses — area, production, yield (p.xii)
- 2023-24 (all pulses): Area 858 '000 acres; Production 429 '000 M.Ton.
- Yield ≈ 429 ÷ 858 ≈ **0.50 ton/acre** (pulses aggregate; lentil/Masur is the largest pulse — use ~0.5 ton/acre as a rough lentil baseline).

## Jute — area, production, yield (p.xii)
- 2023-24: Area 1,788 '000 acres; Production 9,581 '000 bales.
- **Unit caution: jute production is in BALES, not M.Ton** (1 bale ≈ 182 kg). Yield ≈ 9,581 ÷ 1,788 ≈ **5.36 bales/acre** ≈ 0.98 ton/acre. Convert before using in a taka/kg profit calc.

## Using these baselines
- For a profit estimate: expected_yield ≈ national yield above, adjusted up for HYV/hybrid + full FRG fertilizer + good irrigation, or down for local varieties / rainfed / low input.
- Revenue = expected_yield (ton/acre) × farm area (acre) × market price (taka/ton) — pair with the DAM market-price file for price.
- BBS also tabulates crop DAMAGE by flood/cyclone by district (Tables 4.2.x, p.410+) — useful later for a district climate-risk adjustment.
