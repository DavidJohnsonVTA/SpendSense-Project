from __future__ import annotations
import pandas as pd
import streamlit as st
from .summarize import monthly_summary_text

def prepare_items(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return items
    items = items.copy()
    items["date"] = pd.to_datetime(items["date"], errors="coerce")
    items["item_price"] = pd.to_numeric(items["item_price"], errors="coerce").fillna(0)
    items["month"] = items["date"].dt.to_period("M").astype(str)
    return items.dropna(subset=["date"])

def render_dashboard(items: pd.DataFrame) -> None:
    st.header("Monthly Expense Dashboard")
    items = prepare_items(items)
    if items.empty:
        st.info("No saved data yet. Upload a receipt or use the sample CSV files included in data/.")
        return

    months = sorted(items["month"].unique(), reverse=True)
    selected_month = st.selectbox("Month", months)
    month_items = items[items["month"] == selected_month].copy()

    total = month_items["item_price"].sum()
    food = month_items.loc[month_items["summary_group"] == "Total Food", "item_price"].sum()
    groceries = month_items.loc[month_items["category"] == "Groceries", "item_price"].sum()
    dining = month_items.loc[month_items["category"] == "Dining Out", "item_price"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total spending", f"${total:,.2f}")
    c2.metric("Total food", f"${food:,.2f}")
    c3.metric("Groceries", f"${groceries:,.2f}")
    c4.metric("Dining out", f"${dining:,.2f}")

    st.subheader("Spending by category")
    category_totals = month_items.groupby("category")["item_price"].sum().sort_values(ascending=False)
    st.bar_chart(category_totals)

    st.subheader("Spending by merchant")
    merchant_totals = month_items.groupby("merchant")["item_price"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(merchant_totals)

    st.subheader("Weekly trend")
    weekly = month_items.set_index("date").resample("W")["item_price"].sum()
    st.line_chart(weekly)

    st.subheader("Plain-English summary")
    st.write(monthly_summary_text(month_items, selected_month))

    with st.expander("View itemized data"):
        st.dataframe(month_items.drop(columns=["month"], errors="ignore"), use_container_width=True)
