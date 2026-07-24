# Extraction prompt — BARI Krishi Projukti Hatboi (Handbook of Agro-Technology)

**Read `_SHARED_RULES.md` first, then do the following.**

- **Source PDF:** `pdfs/BARI_Krishi_Projukti_Hatboi.pdf` (650 pages, Bangla)
- **Org:** Bangladesh Agricultural Research Institute (BARI), `www.bari.gov.bd`
- **Save output to:** `backend/data/kb/crop_technology.md`

## ⚠️ CRITICAL — DO NOT TRUST THE PDF TEXT LAYER
This PDF's embedded text is a **legacy Bijoy/ASCII-mapped Bangla font**. Copy-pasting or
plain text extraction produces GARBAGE (e.g. `weGAviAvB D™¢vweZ dm‡ji RvZmg~n`). You MUST
**render each page as an image and read it visually (OCR / vision)**, then transcribe the
real Bangla and translate to English. Ignore any extracted text stream entirely.

If your tool cannot do vision/OCR on rendered pages, STOP and report that — do not output
the garbled text.

## What to extract
This handbook has a package of practice per crop. For each crop below, create one
`## <Crop> — cultivation` section (split into parts if long) with:
- **Recommended varieties** (BARI variety names + 1-line trait, e.g. "BARI Alu-25 = high yield").
- **Sowing / planting window** (months / season).
- **Seed rate** (per hectare or per acre — keep unit).
- **Spacing** (row × plant, in cm).
- **Fertilizer dose + timing** (only if given here; FRG is the primary fertilizer source).
- **Irrigation** count / critical stages.
- **Major pests & diseases** + control.
- **Harvest time** (days after sowing / month).
Cite page numbers.

## Crops to cover (find their chapters; these are the highest value)
Potato (Aloo), Maize (Bhutta), Wheat (Gom), Onion (Piaj), Tomato, Brinjal (Begun),
Mustard (Sarisha), Lentil (Masur). (Rice is covered by BRRI/other docs — skip rice here.)

Do the 4–5 most complete crops well rather than all 8 poorly. Faithful numbers matter more
than coverage.
