# Extraction prompt — BRRI Rice Cultivation Guide  (⏳ awaiting PDF)

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/BRRI_Rice_Guide.pdf`  ← save the download here with this exact name
- **Org:** Bangladesh Rice Research Institute (BRRI), `www.brri.gov.bd`
  (e.g. "Adhunik Dhaner Chash" / Modern Rice Cultivation booklet, or BRRI production guide)
- **Save output to:** `backend/data/kb/rice_cultivation.md`
- **Why:** rice is Bangladesh's #1 crop but `crop_technology.md` (BARI) skips rice. This fills it.

## ⚠️ Likely Bangla + legacy font
BRRI booklets are often Bangla with the same broken-font problem as the BARI handbook.
**Render pages as images and use vision/OCR**, do not trust the extracted text stream.
If it's actually a clean English BRRI publication, normal extraction is fine.

## What to extract
One `## <Season> rice` section for each of **Boro, Aman (T. Aman), Aus**, each with:
- **Recommended BRRI varieties** (BRRI dhan28, 29, 89, 92, etc.) + 1-line trait & duration (days).
- **Seedbed + transplanting window** (dates/months), seedling age.
- **Spacing** and seedling/hill.
- **Fertilizer timing/splits** (defer exact doses to FRG; capture the split schedule).
- **Water management** (AWD / continuous flooding, critical stages).
- **Major pests & diseases by stage** (stem borer, BPH, blast, sheath blight) + control.
- **Harvest** timing / maturity signs.
Cite page numbers. Keep durations and dates exact.
