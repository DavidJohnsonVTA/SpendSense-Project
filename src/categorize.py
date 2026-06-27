from pathlib import Path
import pandas as pd
from .schema import SUMMARY_GROUPS

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "category_rules.csv"

def load_rules(path: Path = DEFAULT_RULES_PATH) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=["keyword", "category", "summary_group"])

def categorize_item(item_name: str, current_category: str = "Miscellaneous", rules: pd.DataFrame | None = None) -> tuple[str, str]:
    """Rules-first categorization. Keeps AI category unless a keyword rule is found."""
    if rules is None:
        rules = load_rules()
    text = str(item_name).lower()
    for _, row in rules.iterrows():
        keyword = str(row.get("keyword", "")).lower().strip()
        if keyword and keyword in text:
            category = str(row.get("category", "Miscellaneous"))
            return category, SUMMARY_GROUPS.get(category, str(row.get("summary_group", "Miscellaneous")))
    category = current_category if current_category in SUMMARY_GROUPS else "Miscellaneous"
    return category, SUMMARY_GROUPS.get(category, "Miscellaneous")
