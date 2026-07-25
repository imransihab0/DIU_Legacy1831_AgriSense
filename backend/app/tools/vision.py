"""Plant disease/pest diagnosis from a leaf photo (Tier 2, LLM vision).

The farmer uploads a leaf image; we send it to the vision model with a Bangladesh
crop-pathology prompt and return an honest, actionable assessment. Clearly labeled as
an AI VISUAL assessment (not a lab test) — the treatment is grounded against the pest
knowledge base by the agent on follow-up.
"""
from openai import OpenAI
from .. import config, state

_SYSTEM = """You are a plant pathologist for Bangladeshi crops. Look at the farmer's leaf/plant photo and give a SHORT, practical assessment:
1. Crop (if identifiable) and the plant part shown.
2. Most likely disease or pest — name it (English + common Bengali name).
3. Confidence: low / medium / high — be honest; if the photo is blurry/unclear or not a plant, say so and ask for a clearer photo.
4. Visible symptoms you actually see in THIS photo (spots, colour, pattern) — don't invent.
5. Immediate action + simple prevention. Name a common product only if clearly warranted (e.g. mancozeb for many fungal blights).
Reply in the farmer's language (Bengali if the note is Bengali, else English). Keep it to a few short lines.
END with one line: "⚠️ এটি ছবি দেখে AI-এর ধারণা, ল্যাব পরীক্ষা নয় — নিশ্চিত হতে স্থানীয় কৃষি অফিস/DAE-তে দেখান।" (or the English equivalent).
Never claim certainty you don't have."""


def diagnose_leaf(image_data_url: str, note: str = "") -> dict:
    """Diagnose a crop leaf photo. image_data_url is a data: URI (jpeg/png, base64)."""
    if not image_data_url.startswith("data:image"):
        return {"error": "Expected an image data URL."}
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": note or "আমার ফসলের পাতা/গাছ দেখে রোগ বা পোকা শনাক্ত করুন।"},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ]},
            ],
            max_tokens=600,  # Bengali needs more tokens; 300 truncated the diagnosis mid-sentence
        )
        return {"diagnosis": resp.choices[0].message.content or "", "source": "AI visual assessment (vision model)"}
    except Exception as e:
        return {"error": f"Vision API Error: {type(e).__name__} - {str(e)}. Tell the farmer the image processing failed due to a technical error."}
