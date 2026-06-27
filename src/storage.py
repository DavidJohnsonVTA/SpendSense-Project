from __future__ import annotations
from pathlib import Path
from datetime import datetime
import uuid
import pandas as pd
from .schema import SUMMARY_GROUPS

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RECEIPTS_CSV = DATA_DIR / "receipts.csv"
ITEMS_CSV = DATA_DIR / "receipt_items.csv"

RECEIPT_COLUMNS = [
    "receipt_id", "date", "merchant", "subtotal", "tax", "tip", "total", "payment_method", "notes", "image_filename", "created_at"
]
ITEM_COLUMNS = [
    "receipt_id", "date", "merchant", "item_name", "item_price", "category", "summary_group", "confidence", "user_corrected"
]

def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not RECEIPTS_CSV.exists():
        pd.DataFrame(columns=RECEIPT_COLUMNS).to_csv(RECEIPTS_CSV, index=False)
    if not ITEMS_CSV.exists():
        pd.DataFrame(columns=ITEM_COLUMNS).to_csv(ITEMS_CSV, index=False)

def load_receipts(use_sample_if_empty: bool = True) -> pd.DataFrame:
    ensure_data_files()
    df = pd.read_csv(RECEIPTS_CSV)
    sample = DATA_DIR / "sample_receipts.csv"
    if use_sample_if_empty and df.empty and sample.exists():
        return pd.read_csv(sample)
    return df

def load_items(use_sample_if_empty: bool = True) -> pd.DataFrame:
    ensure_data_files()
    df = pd.read_csv(ITEMS_CSV)
    sample = DATA_DIR / "sample_receipt_items.csv"
    if use_sample_if_empty and df.empty and sample.exists():
        return pd.read_csv(sample)
    return df

def save_receipt(receipt: dict, items_df: pd.DataFrame, image_filename: str = "") -> str:
    ensure_data_files()
    receipt_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat(timespec="seconds")

    receipt_row = {
        "receipt_id": receipt_id,
        "date": receipt.get("date") or datetime.now().date().isoformat(),
        "merchant": receipt.get("merchant", "Unknown Merchant"),
        "subtotal": float(receipt.get("subtotal", 0) or 0),
        "tax": float(receipt.get("tax", 0) or 0),
        "tip": float(receipt.get("tip", 0) or 0),
        "total": float(receipt.get("total", 0) or 0),
        "payment_method": receipt.get("payment_method") or "",
        "notes": receipt.get("notes") or "",
        "image_filename": image_filename,
        "created_at": created_at,
    }

    receipts_df = pd.read_csv(RECEIPTS_CSV)
    receipts_df = pd.concat([receipts_df, pd.DataFrame([receipt_row])], ignore_index=True)
    receipts_df.to_csv(RECEIPTS_CSV, index=False)

    cleaned_items = []
    for _, row in items_df.iterrows():
        category = str(row.get("category", "Miscellaneous"))
        cleaned_items.append({
            "receipt_id": receipt_id,
            "date": receipt_row["date"],
            "merchant": receipt_row["merchant"],
            "item_name": row.get("item_name", "Unknown Item"),
            "item_price": float(row.get("item_price", 0) or 0),
            "category": category,
            "summary_group": SUMMARY_GROUPS.get(category, "Miscellaneous"),
            "confidence": float(row.get("confidence", 0.5) or 0.5),
            "user_corrected": bool(row.get("user_corrected", False)),
        })

    existing_items = pd.read_csv(ITEMS_CSV)
    new_items = pd.DataFrame(cleaned_items, columns=ITEM_COLUMNS)
    all_items = pd.concat([existing_items, new_items], ignore_index=True)
    all_items.to_csv(ITEMS_CSV, index=False)
    return receipt_id
