from __future__ import annotations
import pandas as pd
import streamlit as st
from src.ai_extract import extract_receipt_from_image, demo_receipt
from src.categorize import categorize_item, load_rules
from src.dashboard import render_dashboard
from src.schema import CATEGORIES
from src.storage import load_items, load_receipts, save_receipt
from src.validate import validate_receipt_totals

st.set_page_config(page_title="SpendSense", page_icon="🧾", layout="wide")
st.title("SpendSense: AI Receipt Scanner & Expense Dashboard")
st.caption("Upload receipts, review extracted items, save categorized expenses, and track monthly spending.")

with st.sidebar:
    st.header("Build stages")
    st.markdown(
        """
        1. Dashboard from sample CSV  
        2. Receipt upload  
        3. Gemini extraction  
        4. Review/edit table  
        5. Save to CSV  
        6. Monthly summary
        """
    )
    use_demo = st.toggle("Use demo receipt instead of API", value=False)

upload_tab, dashboard_tab, data_tab = st.tabs(["Scan receipt", "Dashboard", "Saved data"])

with upload_tab:
    st.header("1. Upload a receipt")
    uploaded_file = st.file_uploader("Choose a receipt image", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded receipt", width=350)

    extract_clicked = st.button("Extract receipt data", type="primary", disabled=(uploaded_file is None and not use_demo))

    if extract_clicked:
        try:
            if use_demo:
                receipt_data = demo_receipt()
            else:
                image_bytes = uploaded_file.getvalue()
                receipt_data = extract_receipt_from_image(image_bytes, uploaded_file.type)
            st.session_state["receipt"] = receipt_data.model_dump()
        except Exception as exc:
            st.error(str(exc))

    if "receipt" in st.session_state:
        receipt = st.session_state["receipt"]
        st.header("2. Review receipt details")
        c1, c2, c3 = st.columns(3)
        receipt["merchant"] = c1.text_input("Merchant", receipt.get("merchant", "Unknown Merchant"))
        receipt["date"] = c2.text_input("Date YYYY-MM-DD", receipt.get("date") or "")
        receipt["payment_method"] = c3.text_input("Payment method", receipt.get("payment_method") or "")

        c4, c5, c6, c7 = st.columns(4)
        receipt["subtotal"] = c4.number_input("Subtotal", min_value=0.0, value=float(receipt.get("subtotal", 0) or 0), step=0.01)
        receipt["tax"] = c5.number_input("Tax", min_value=0.0, value=float(receipt.get("tax", 0) or 0), step=0.01)
        receipt["tip"] = c6.number_input("Tip", min_value=0.0, value=float(receipt.get("tip", 0) or 0), step=0.01)
        receipt["total"] = c7.number_input("Total", min_value=0.0, value=float(receipt.get("total", 0) or 0), step=0.01)

        st.header("3. Review and edit item categories")
        rules = load_rules()
        item_rows = []
        for item in receipt.get("items", []):
            category, summary_group = categorize_item(item.get("name", ""), item.get("category", "Miscellaneous"), rules)
            item_rows.append({
                "item_name": item.get("name", "Unknown Item"),
                "item_price": float(item.get("price", 0) or 0),
                "category": category,
                "summary_group": summary_group,
                "confidence": float(item.get("confidence", 0.5) or 0.5),
                "user_corrected": False,
            })

        items_df = pd.DataFrame(item_rows)
        edited_df = st.data_editor(
            items_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES),
                "item_price": st.column_config.NumberColumn("Price", min_value=0.0, step=0.01, format="$%.2f"),
                "confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0),
            },
        )

        warnings = validate_receipt_totals(
            edited_df.to_dict("records"), receipt.get("subtotal", 0), receipt.get("tax", 0), receipt.get("tip", 0), receipt.get("total", 0)
        )
        for warning in warnings:
            st.warning(warning)

        save_disabled = edited_df.empty
        if st.button("Save approved receipt", disabled=save_disabled):
            image_name = uploaded_file.name if uploaded_file else "demo"
            receipt_id = save_receipt(receipt, edited_df, image_name)
            st.success(f"Saved receipt {receipt_id}. Open the Dashboard tab to see updated totals.")
            del st.session_state["receipt"]

with dashboard_tab:
    render_dashboard(load_items(use_sample_if_empty=True))

with data_tab:
    st.header("Saved receipts")
    st.dataframe(load_receipts(use_sample_if_empty=True), use_container_width=True)
    st.header("Saved receipt items")
    st.dataframe(load_items(use_sample_if_empty=True), use_container_width=True)
    st.caption("Note: sample data is displayed until you save your first real receipt.")
