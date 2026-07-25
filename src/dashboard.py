from __future__ import annotations

import pandas as pd
import streamlit as st

from src.summarize import build_monthly_summary


def _prepare_items_df(items_df: pd.DataFrame) -> pd.DataFrame:
    df = items_df.copy()

    if df.empty:
        return df

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "item_price" in df.columns:
        df["item_price"] = pd.to_numeric(df["item_price"], errors="coerce").fillna(0)
    else:
        df["item_price"] = 0.0

    if "allocated_price" in df.columns:
        df["allocated_price"] = pd.to_numeric(df["allocated_price"], errors="coerce")
        df["dashboard_amount"] = df["allocated_price"].fillna(df["item_price"])
    else:
        df["dashboard_amount"] = df["item_price"]

    df["dashboard_amount"] = pd.to_numeric(
        df["dashboard_amount"], errors="coerce"
    ).fillna(0)

    for col in ["category", "summary_group", "merchant", "item_name"]:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown").astype(str)

    return df


def render_dashboard(items_df: pd.DataFrame) -> None:
    st.header("Monthly Expense Dashboard")

    if items_df is None or items_df.empty:
        st.info("No receipt item data available yet.")
        return

    df = _prepare_items_df(items_df)

    if df.empty:
        st.info("No receipt item data available yet.")
        return

    if "date" in df.columns and df["date"].notna().any():
        df["month"] = df["date"].dt.to_period("M").astype(str)
        months = sorted(df["month"].dropna().unique(), reverse=True)

        selected_month = st.selectbox(
            "Select month",
            months,
            index=0,
            key="dashboard_month_selector",
        )

        month_df = df[df["month"] == selected_month].copy()
    else:
        month_df = df.copy()

    if month_df.empty:
        st.info("No data found for the selected month.")
        return

    total_spent = float(month_df["dashboard_amount"].sum())

    food_df = month_df[
        month_df["category"].isin(["Groceries", "Dining Out"])
        | month_df["summary_group"].eq("Food")
    ]

    total_food = float(food_df["dashboard_amount"].sum())

    groceries = float(
        month_df.loc[month_df["category"] == "Groceries", "dashboard_amount"].sum()
    )

    dining_out = float(
        month_df.loc[month_df["category"] == "Dining Out", "dashboard_amount"].sum()
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total spent", f"${total_spent:,.2f}")
    c2.metric("Total food", f"${total_food:,.2f}")
    c3.metric("Groceries", f"${groceries:,.2f}")
    c4.metric("Dining out", f"${dining_out:,.2f}")

    st.caption(
        "Dashboard totals use allocated receipt amounts when available, so spending reflects "
        "the final charged amount instead of only the pre-tax or pre-discount subtotal."
    )

    st.divider()

    st.subheader("Spending by category")
    category_totals = (
        month_df.groupby("category", as_index=False)["dashboard_amount"]
        .sum()
        .sort_values("dashboard_amount", ascending=False)
    )

    st.bar_chart(
        category_totals.set_index("category")["dashboard_amount"],
        use_container_width=True,
    )

    st.dataframe(
        category_totals.rename(columns={"dashboard_amount": "amount"}),
        use_container_width=True,
    )

    st.subheader("Spending by summary group")
    group_totals = (
        month_df.groupby("summary_group", as_index=False)["dashboard_amount"]
        .sum()
        .sort_values("dashboard_amount", ascending=False)
    )

    st.bar_chart(
        group_totals.set_index("summary_group")["dashboard_amount"],
        use_container_width=True,
    )

    st.subheader("Spending by merchant")
    merchant_totals = (
        month_df.groupby("merchant", as_index=False)["dashboard_amount"]
        .sum()
        .sort_values("dashboard_amount", ascending=False)
    )

    st.dataframe(
        merchant_totals.rename(columns={"dashboard_amount": "amount"}),
        use_container_width=True,
    )

    if "date" in month_df.columns and month_df["date"].notna().any():
        st.subheader("Weekly spending trend")

        weekly = (
            month_df.set_index("date")
            .resample("W")["dashboard_amount"]
            .sum()
            .reset_index()
        )

        weekly["week"] = weekly["date"].dt.strftime("%Y-%m-%d")

        st.line_chart(
            weekly.set_index("week")["dashboard_amount"],
            use_container_width=True,
        )

    st.subheader("Largest item-level charges")
    top_items = month_df.sort_values("dashboard_amount", ascending=False).head(10)

    display_cols = [
        "date",
        "merchant",
        "item_name",
        "category",
        "item_price",
        "dashboard_amount",
    ]

    existing_cols = [col for col in display_cols if col in top_items.columns]

    st.dataframe(
        top_items[existing_cols].rename(
            columns={
                "item_price": "original_item_price",
                "dashboard_amount": "allocated_dashboard_amount",
            }
        ),
        use_container_width=True,
    )

    st.divider()

    st.subheader("Monthly summary")
    summary = build_monthly_summary(month_df, amount_column="dashboard_amount")
    st.write(summary)