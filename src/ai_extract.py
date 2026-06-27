from __future__ import annotations
import json
import os
import re
from typing import Any
from dotenv import load_dotenv
from pydantic import ValidationError
from .schema import ReceiptData, CATEGORIES

load_dotenv()

RECEIPT_PROMPT = f"""
You extract structured expense data from receipt images.
Return ONLY valid JSON. Do not include markdown, comments, or extra text.

Use this exact shape:
{{
  "merchant": "string",
  "date": "YYYY-MM-DD or null",
  "items": [
    {{"name": "string", "price": 0.00, "category": "one category", "confidence": 0.0}}
  ],
  "subtotal": 0.00,
  "tax": 0.00,
  "tip": 0.00,
  "total": 0.00,
  "payment_method": "string or null",
  "notes": "string or null"
}}

Allowed item categories: {', '.join(CATEGORIES)}.
Rules:
- Extract line items when readable.
- Do not invent item names or prices.
- Use Miscellaneous when uncertain.
- Use Dining Out for restaurants, cafes, coffee shops, and takeout.
- Use Groceries for food bought at grocery stores.
- Use Household for cleaning supplies, paper goods, home supplies.
- Use School for notebooks, supplies, textbooks, printing, student expenses.
- If a date is ambiguous or missing, use null.
- Confidence should reflect extraction/categorization certainty from 0 to 1.
"""

def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text

def parse_receipt_json(raw_text: str) -> ReceiptData:
    json_text = _extract_json(raw_text)
    data = json.loads(json_text)
    return ReceiptData.model_validate(data)

def extract_receipt_from_image(image_bytes: bytes, mime_type: str) -> ReceiptData:
    """Uses Gemini multimodal input to extract receipt JSON."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY. Copy .env.example to .env and add your key.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Run: pip install -r requirements.txt") from exc

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = client.models.generate_content(
        model=model,
        contents=[
            RECEIPT_PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    try:
        return parse_receipt_json(response.text or "{}")
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(f"The model returned invalid receipt JSON: {response.text}") from exc

def demo_receipt() -> ReceiptData:
    """Fallback data so the UI can be tested before API setup."""
    return ReceiptData.model_validate({
        "merchant": "Target",
        "date": "2026-01-18",
        "items": [
            {"name": "Milk", "price": 4.29, "category": "Groceries", "confidence": 0.91},
            {"name": "Laundry Detergent", "price": 12.49, "category": "Household", "confidence": 0.88},
            {"name": "Notebook", "price": 2.99, "category": "School", "confidence": 0.86},
        ],
        "subtotal": 19.77,
        "tax": 1.62,
        "tip": 0,
        "total": 21.39,
        "payment_method": "Credit",
        "notes": "Demo receipt. Replace with real extraction after API setup."
    })
