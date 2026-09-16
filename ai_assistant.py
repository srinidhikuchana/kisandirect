import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "te": "Telugu"}


async def explain_analysis(crop: str, analysis: dict, language: str = "en") -> str:
    """Turn a market-analysis result into a short farmer-friendly explanation
    in the requested language, using OpenRouter. Falls back to the raw demo
    explanation if no API key is configured or the call fails."""
    fallback = analysis.get("explanation", "")

    if not OPENROUTER_API_KEY:
        return fallback + "\n\n(Set OPENROUTER_API_KEY in .env to get this explained in Hindi/Telugu by AI.)"

    lang_name = LANGUAGE_NAMES.get(language, "English")
    system_prompt = (
        "You are AgriNexus's assistant for Indian farmers. Explain market analysis "
        "results in simple, plain-spoken " + lang_name + ". Keep it under 80 words, "
        "no jargon, practical tone. Use the given numbers, don't invent new ones."
    )
    user_prompt = (
        f"Crop: {crop}\n"
        f"Demand: {analysis.get('demand')}\n"
        f"Suggested price: Rs {analysis.get('suggested_price')}/kg\n"
        f"Matched quantity: {analysis.get('matched_quantity')} kg\n"
        f"Estimated revenue: Rs {analysis.get('estimated_revenue')}\n"
        f"Buyer saving vs traditional chain: {analysis.get('buyer_saving_pct')}%\n"
        f"Explain this to the farmer in {lang_name}."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for attribution/rate limits:
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:5500"),
        "X-Title": "AgriNexus",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return fallback + f"\n\n(AI explanation unavailable right now: {e})"


async def chat(messages: list, language: str = "en") -> str:
    """General-purpose multilingual chat for the assistant widget."""
    if not OPENROUTER_API_KEY:
        return "AI assistant isn't configured yet. Add OPENROUTER_API_KEY in .env to enable it."

    lang_name = LANGUAGE_NAMES.get(language, "English")
    system_prompt = (
        "You are AgriNexus's in-app assistant, helping Indian farmers and buyers "
        f"understand produce pricing, demand and logistics. Reply in {lang_name}, "
        "keep answers short and practical."
    )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:5500"),
        "X-Title": "AgriNexus",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_tokens": 400,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI assistant error: {e}"
