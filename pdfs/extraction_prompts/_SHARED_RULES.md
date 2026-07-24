# Shared extraction rules (read first — applies to EVERY prompt in this folder)

You are extracting data from an official Bangladesh agriculture PDF into a clean Markdown
knowledge-base file for a RAG (retrieval) system. Another AI (this one) has already decided
what to pull; your job is faithful extraction + formatting, **not** analysis or opinion.

## Output format (MANDATORY)
1. Produce **one** Markdown file. Save it at the exact path given in each prompt
   (always under `backend/data/kb/`).
2. Begin the file with a citation header, exactly this shape:
   ```
   <!-- SOURCE: <Title> | <Organization> | <Year> | <URL or "official gov publication"> | REAL public source -->
   # <Human title>
   ```
3. Split the body into `## ` sections — **one topic/crop/region per `## ` heading.**
   This is critical: the RAG chunker splits on `## `, so each section must be
   self-contained and make sense on its own. Keep each section roughly **under 1000
   characters**; if a topic is bigger, break it into `## Crop — part 2` etc.
4. Inside a section use short lines / bullet lists, not long paragraphs.

## Accuracy rules (MANDATORY — this is what the judges score)
- **Copy every number exactly.** Doses, prices, yields, dates. Do NOT round, average,
  or invent. Keep the **original unit** (kg/ha vs kg/acre vs kg/bigha) and label it.
  If both units appear, keep both.
- **Cite the page** inline where a fact came from, like `(p.45)`.
- **Translate Bangla → English.** Keep the Bangla/local crop name in parentheses on first
  use, e.g. `Potato (Aloo)`, `Mustard (Sarisha)`, `Boro rice (Boro dhan)`.
- If something is unreadable, write `[illegible]` — never guess.
- No preamble, no "here is your file", no commentary. Just the Markdown file content.

## Scope discipline
- Only extract what the per-PDF prompt asks for. These PDFs are large; do **not** try to
  transcribe everything. Target the specified crops/tables/sections and stop.
- Prefer the crops most relevant to Bangladeshi smallholders: Boro/Aman/Aus rice, wheat,
  maize, potato, mustard, lentil, onion, tomato, brinjal, jute.
