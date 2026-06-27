from __future__ import annotations
import pandas as pd

def monthly_summary_text(items: pd.DataFrame, selected_month: str) -> str:
    if items.empty:
        return "No spending data is available for this month yet."

    total = items["item_price"].sum()
    by_category = items.groupby("category")["item_price"].sum().sort_values(ascending=False)
    by_group = items.groupby("summary_group")["item_price"].sum().sort_values(ascending=False)
    top_category = by_category.index[0]
    top_category_amount = by_category.iloc[0]
    top_merchant = items.groupby("merchant")["item_price"].sum().sort_values(ascending=False).index[0]
    top_merchant_amount = items.groupby("merchant")["item_price"].sum().sort_values(ascending=False).iloc[0]

    food_total = float(by_group.get("Total Food", 0))
    groceries = float(by_category.get("Groceries", 0))
    dining = float(by_category.get("Dining Out", 0))

    return (
        f"In {selected_month}, you recorded ${total:,.2f} in itemized spending. "
        f"Your largest category was {top_category} at ${top_category_amount:,.2f}. "
        f"Total food spending was ${food_total:,.2f}, split between ${groceries:,.2f} in groceries "
        f"and ${dining:,.2f} dining out. Your highest-spend merchant was {top_merchant} "
        f"at ${top_merchant_amount:,.2f}. Review Miscellaneous items to improve future categorization."
    )
