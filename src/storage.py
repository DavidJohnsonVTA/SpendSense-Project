from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
RECEIPTS_PATH = DATA_DIR / "receipts.csv"
ITEMS_PATH = DATA_DIR / "receipt_items.csv"
SAMPLE_RECEIPTS_PATH = DATA_DIR / "sample_receipts.csv"
SAMPLE_ITEMS_PATH = DATA_DIR / "sample_receipt_items.csv"


RECEIPT_COLUMNS = [
    "receipt_id",
    "date",
    "merchant",
    "subtotal",
    "tax",
    "tip",
    "total",
    "payment_method",
    "notes",
    "image_filename",
    "created_at",
]


ITEM_COLUMNS = [
    "item_id",
    "receipt_id",
    "date",
    "merchant",
    "item_name",
    "item_price",
    "category",
    "summary_group",
    "confidence",
    "user_corrected",
    "allocated_price",
]


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def _read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)


def load_receipts(use_sample_if_empty: bool = False) -> pd.DataFrame:
    receipts = _read_csv(RECEIPTS_PATH, RECEIPT_COLUMNS)

    if receipts.empty and use_sample_if_empty and SAMPLE_RECEIPTS_PATH.exists():
        return _read_csv(SAMPLE_RECEIPTS_PATH, RECEIPT_COLUMNS)

    return receipts


def load_items(use_sample_if_empty: bool = False) -> pd.DataFrame:
    items = _read_csv(ITEMS_PATH, ITEM_COLUMNS)

    if items.empty and use_sample_if_empty and SAMPLE_ITEMS_PATH.exists():
        return _read_csv(SAMPLE_ITEMS_PATH, ITEM_COLUMNS)

    return items


def save_receipt(receipt: dict, edited_df: pd.DataFrame, image_name: str) -> str:
    """
    Saves one receipt locally to CSV.

    The dashboard should use allocated_price when available so category totals
    add up to the final charged receipt total, not just the raw item subtotal.
    """
    _ensure_data_dir()

    receipt_id = str(uuid.uuid4())[:8]
    created_at = pd.Timestamp.now().isoformat()

    receipt_row = {
        "receipt_id": receipt_id,
        "date": receipt.get("date", ""),
        "merchant": receipt.get("merchant", "Unknown Merchant"),
        "subtotal": float(receipt.get("subtotal", 0) or 0),
        "tax": float(receipt.get("tax", 0) or 0),
        "tip": float(receipt.get("tip", 0) or 0),
        "total": float(receipt.get("total", 0) or 0),
        "payment_method": receipt.get("payment_method", ""),
        "notes": receipt.get("notes", ""),
        "image_filename": image_name,
        "created_at": created_at,
    }

    receipts_df = load_receipts(use_sample_if_empty=False)
    receipts_df = pd.concat(
        [receipts_df, pd.DataFrame([receipt_row])],
        ignore_index=True,
    )
    receipts_df.to_csv(RECEIPTS_PATH, index=False)

    item_subtotal = float(pd.to_numeric(edited_df["item_price"], errors="coerce").fillna(0).sum())
    receipt_total = float(receipt.get("total", 0) or 0)

    if item_subtotal > 0 and receipt_total > 0:
        allocation_factor = receipt_total / item_subtotal
    else:
        allocation_factor = 1.0

    item_rows = []

    for index, item in edited_df.reset_index(drop=True).iterrows():
        item_price = float(item.get("item_price", 0) or 0)
        allocated_price = round(item_price * allocation_factor, 2)

        item_rows.append(
            {
                "item_id": f"{receipt_id}-{index + 1}",
                "receipt_id": receipt_id,
                "date": receipt.get("date", ""),
                "merchant": receipt.get("merchant", "Unknown Merchant"),
                "item_name": item.get("item_name", "Unknown Item"),
                "item_price": item_price,
                "category": item.get("category", "Miscellaneous"),
                "summary_group": item.get("summary_group", "Other"),
                "confidence": float(item.get("confidence", 0.5) or 0.5),
                "user_corrected": bool(item.get("user_corrected", False)),
                "allocated_price": allocated_price,
            }
        )

    items_df = load_items(use_sample_if_empty=False)
    items_df = pd.concat([items_df, pd.DataFrame(item_rows)], ignore_index=True)
    items_df.to_csv(ITEMS_PATH, index=False)

    return receipt_id