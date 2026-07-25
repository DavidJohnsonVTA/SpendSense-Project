from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.schema import CATEGORIES, CATEGORY_TO_SUMMARY_GROUP


RULES_PATH = Path("data/category_rules.csv")


def load_rules() -> list[dict]:
    """
    Loads optional category rules from data/category_rules.csv.

    Expected columns:
      keyword, category, summary_group

    If the file is missing or malformed, the app still works using AI-suggested
    categories and default category-to-summary-group mapping.
    """
    if not RULES_PATH.exists():
        return []

    try:
        df = pd.read_csv(RULES_PATH)
    except Exception:
        return []

    required = {"keyword", "category"}
    if not required.issubset(set(df.columns)):
        return []

    rules = []

    for _, row in df.iterrows():
        keyword = str(row.get("keyword", "")).strip().lower()
        category = str(row.get("category", "Miscellaneous")).strip()
        summary_group = str(row.get("summary_group", "")).strip()

        if not keyword:
            continue

        if category not in CATEGORIES:
            category = "Miscellaneous"

        if not summary_group:
            summary_group = CATEGORY_TO_SUMMARY_GROUP.get(category, "Other")

        rules.append(
            {
                "keyword": keyword,
                "category": category,
                "summary_group": summary_group,
            }
        )

    return rules


def categorize_item(
    item_name: str,
    suggested_category: str = "Miscellaneous",
    rules: list[dict] | None = None,
) -> tuple[str, str]:
    """
    Returns:
      category, summary_group

    Priority:
      1. Keyword rules from category_rules.csv
      2. AI-suggested category if valid
      3. Miscellaneous fallback
    """
    rules = rules or []
    item_text = str(item_name or "").lower()

    for rule in rules:
        keyword = str(rule.get("keyword", "")).lower().strip()

        if keyword and keyword in item_text:
            category = rule.get("category", "Miscellaneous")

            if category not in CATEGORIES:
                category = "Miscellaneous"

            summary_group = rule.get("summary_group") or CATEGORY_TO_SUMMARY_GROUP.get(
                category,
                "Other",
            )

            return category, summary_group

    category = str(suggested_category or "Miscellaneous").strip()

    if category not in CATEGORIES:
        category = "Miscellaneous"

    summary_group = CATEGORY_TO_SUMMARY_GROUP.get(category, "Other")

    return category, summary_group