from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from src.schema import Receipt

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError as exc:
    raise ImportError(
        "google-genai is not installed. Run: pip install -r requirements.txt"
    ) from exc


RECEIPT_EXTRACTION_PROMPT = """
You are extracting structured data from a retail or restaurant receipt image.

Return ONLY valid JSON. Do not include markdown, commentary, or explanation.

Important accounting rules:
- The field "subtotal" should be the pre-tax or pre-adjustment subtotal when visible.
- The field "total" must be the final charged amount, final amount paid, or card charge.
- If the receipt shows both a subtotal and a final total, DO NOT use subtotal as total.
- If discounts, coupons, rewards, gift cards, tax, bottle deposits, fees, or tips appear,
  the "total" field should reflect the final amount actually paid after those adjustments.
- If multiple possible totals appear, choose the amount closest to "amount paid",
  "total", "card charge", "charged", "payment", or "balance due".
- Item prices should be the visible item-level prices before final receipt-level allocation.
- If item-level discounts are visible, use the discounted item price when clear.
- If an item is unreadable, include your best guess and lower confidence.

Categorize each item into exactly one of these categories:
- Groceries
- Dining Out
- Household
- Transportation
- School
- Health
- Personal Care
- Entertainment
- Clothing
- Bills
- Miscellaneous

Use these summary groups:
- Food
- Essentials
- Lifestyle
- School
- Other

Category guidance:
- Groceries: grocery items, snacks, drinks from grocery/retail stores, ingredients
- Dining Out: restaurants, cafes, fast food, prepared meals from restaurants
- Household: cleaning supplies, paper towels, detergent, home goods
- Transportation: gas, transit, parking, rideshare
- School: notebooks, textbooks, supplies, academic materials
- Health: pharmacy, medicine, first aid
- Personal Care: shampoo, deodorant, skincare, hygiene
- Entertainment: movies, games, events, hobbies
- Clothing: clothes, shoes, accessories
- Bills: utilities, subscriptions, recurring payments
- Miscellaneous: anything unclear

Required JSON shape:
{
  "merchant": "string",
  "date": "YYYY-MM-DD or null",
  "items": [
    {
      "name": "string",
      "price": 0.00,
      "category": "Groceries",
      "summary_group": "Food",
      "confidence": 0.0
    }
  ],
  "subtotal": 0.00,
  "tax": 0.00,
  "tip": 0.00,
  "total": 0.00,
  "payment_method": "string or null",
  "notes": "string"
}
"""


def _get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def _extract_json_text(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Model response did not contain a JSON object.")

    return cleaned[start : end + 1]


def _call_gemini_with_retries(
    client: Any,
    model_name: str,
    contents: list[Any],
    max_retries: int = 3,
):
    last_error = None

    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            last_error = exc
            error_text = str(exc)

            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if temporary_error and attempt < max_retries - 1:
                wait_seconds = 2**attempt
                time.sleep(wait_seconds)
                continue

            raise

    raise RuntimeError("Gemini request failed after retries.") from last_error


def extract_receipt_from_image(image_bytes: bytes, mime_type: str) -> Receipt:
    api_key = _get_secret("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Add it to .env locally or Streamlit Secrets when deployed."
        )

    primary_model = _get_secret("GEMINI_MODEL", "gemini-2.5-flash")
    fallback_model = _get_secret("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")

    client = genai.Client(api_key=api_key)

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type,
    )

    contents = [
        RECEIPT_EXTRACTION_PROMPT,
        image_part,
    ]

    model_errors = []

    for model_name in [primary_model, fallback_model]:
        if not model_name:
            continue

        try:
            response = _call_gemini_with_retries(
                client=client,
                model_name=model_name,
                contents=contents,
            )

            response_text = response.text or ""
            json_text = _extract_json_text(response_text)
            data = json.loads(json_text)

            return Receipt.model_validate(data)

        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise RuntimeError(f"Could not parse receipt data from model output: {exc}") from exc

        except Exception as exc:
            model_errors.append(f"{model_name}: {exc}")
            continue

    raise RuntimeError(
        "Receipt extraction failed for all configured Gemini models. "
        + " | ".join(model_errors)
    )


def demo_receipt() -> Receipt:
    data = {
        "merchant": "Target",
        "date": "2026-01-18",
        "items": [
            {
                "name": "Milk",
                "price": 4.29,
                "category": "Groceries",
                "summary_group": "Food",
                "confidence": 0.92,
            },
            {
                "name": "Laundry Detergent",
                "price": 12.49,
                "category": "Household",
                "summary_group": "Essentials",
                "confidence": 0.91,
            },
            {
                "name": "Notebook",
                "price": 2.99,
                "category": "School",
                "summary_group": "School",
                "confidence": 0.88,
            },
            {
                "name": "Chips",
                "price": 3.99,
                "category": "Groceries",
                "summary_group": "Food",
                "confidence": 0.86,
            },
        ],
        "subtotal": 23.76,
        "tax": 1.62,
        "tip": 0.00,
        "total": 25.38,
        "payment_method": "Card",
        "notes": "Demo receipt for local testing.",
    }

    return Receipt.model_validate(data)