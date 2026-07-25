from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


CATEGORIES = [
    "Groceries",
    "Dining Out",
    "Household",
    "Transportation",
    "School",
    "Health",
    "Personal Care",
    "Entertainment",
    "Clothing",
    "Bills",
    "Miscellaneous",
]


SUMMARY_GROUPS = [
    "Food",
    "Essentials",
    "Lifestyle",
    "School",
    "Other",
]


class ReceiptItem(BaseModel):
    name: str = Field(default="Unknown Item")
    price: float = Field(default=0.0)
    category: str = Field(default="Miscellaneous")
    summary_group: str = Field(default="Other")
    confidence: float = Field(default=0.5)


class Receipt(BaseModel):
    merchant: str = Field(default="Unknown Merchant")
    date: Optional[str] = None
    items: list[ReceiptItem] = Field(default_factory=list)
    subtotal: float = Field(default=0.0)
    tax: float = Field(default=0.0)
    tip: float = Field(default=0.0)
    total: float = Field(default=0.0)
    payment_method: Optional[str] = None
    notes: str = Field(default="")