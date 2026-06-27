from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

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

SUMMARY_GROUPS = {
    "Groceries": "Total Food",
    "Dining Out": "Total Food",
    "Household": "Essentials",
    "Transportation": "Essentials",
    "Bills": "Essentials",
    "Health": "Essentials",
    "School": "School",
    "Personal Care": "Lifestyle",
    "Entertainment": "Lifestyle",
    "Clothing": "Lifestyle",
    "Miscellaneous": "Miscellaneous",
}

class ReceiptItem(BaseModel):
    name: str = Field(description="Item name from the receipt")
    price: float = Field(ge=0, description="Item price as a positive number")
    category: str = Field(default="Miscellaneous")
    confidence: float = Field(default=0.5, ge=0, le=1)

    @field_validator("category")
    @classmethod
    def valid_category(cls, value: str) -> str:
        return value if value in CATEGORIES else "Miscellaneous"

class ReceiptData(BaseModel):
    merchant: str = "Unknown Merchant"
    date: Optional[str] = Field(default=None, description="ISO format date YYYY-MM-DD if visible")
    items: List[ReceiptItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    total: float = 0.0
    payment_method: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("subtotal", "tax", "tip", "total")
    @classmethod
    def non_negative_money(cls, value: float) -> float:
        return max(float(value or 0), 0)
