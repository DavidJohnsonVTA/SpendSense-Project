from __future__ import annotations

import pandas as pd


def _money(value: float) -> str:
    return f"${value:,.2f}"


def build_monthly_summary(
    items_df: pd.DataFrame,
    amount_column: str = "item_price",
) -> str:
    """
    Build a simple monthly spending summary.

    amount_column lets the dashboard use allocated_price/dashboard_amount
    instead of raw item_price, so totals reflect the final charged receipt amount.
    """

    if items_df is None or items_df.empty:
        return "No spending data is available yet."

    df = items_df.copy()

    if amount_column not in df.columns:
        amount_column = "item_price"

    if amount_column not in df.columns:
        return "No spending amount column is available yet."

    df[amount_column] = pd.to_numeric(df[amount_column], errors="coerce").fillna(0)

    for col in ["category", "summary_group", "merchant", "item_name"]:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown").astype(str)

    total_spent = float(df[amount_column].sum())

    category_totals = (
        df.groupby("category")[amount_column]
        .sum()
        .sort_values(ascending=False)
    )

    merchant_totals = (
        df.groupby("merchant")[amount_column]
        .sum()
        .sort_values(ascending=False)
    )

    groceries = float(
        df.loc[df["category"] == "Groceries", amount_column].sum()
    )

    dining_out = float(
        df.loc[df["category"] == "Dining Out", amount_column].sum()
    )

    total_food = groceries + dining_out

    largest_category = (
        category_totals.index[0] if not category_totals.empty else "Unknown"
    )

    largest_category_amount = (
        float(category_totals.iloc[0]) if not category_totals.empty else 0.0
    )

    top_merchant = (
        merchant_totals.index[0] if not merchant_totals.empty else "Unknown"
    )

    top_merchant_amount = (
        float(merchant_totals.iloc[0]) if not merchant_totals.empty else 0.0
    )

    receipt_count = (
        df["receipt_id"].nunique()
        if "receipt_id" in df.columns
        else len(df)
    )

    lines = [
        f"You spent {_money(total_spent)} across {receipt_count} receipt(s) in this view.",
        f"Your largest spending category was {largest_category} at {_money(largest_category_amount)}.",
        f"Food spending totaled {_money(total_food)}, including {_money(groceries)} on groceries and {_money(dining_out)} on dining out.",
        f"Your highest-spend merchant was {top_merchant} at {_money(top_merchant_amount)}.",
    ]

    if len(category_totals) > 0:
        top_categories = category_totals.head(3)
        category_text = ", ".join(
            f"{category}: {_money(float(amount))}"
            for category, amount in top_categories.items()
        )
        lines.append(f"Top categories: {category_text}.")

    return " ".join(lines)