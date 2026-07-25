from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.ai_extract import extract_receipt_from_image, demo_receipt
from src.categorize import categorize_item, load_rules
from src.dashboard import render_dashboard
from src.schema import CATEGORIES
from src.storage import load_items, load_receipts, save_receipt
from src.validate import validate_receipt_totals
from src.google_sheets_storage import (
    append_receipt,
    append_receipt_items,
    read_receipts,
    read_receipt_items,
)

st.set_page_config(page_title="SpendSense", page_icon="🧾", layout="wide")
st.title("SpendSense: AI Receipt Scanner & Expense Dashboard")
st.caption(
    "Upload receipts, review extracted items, save categorized expenses, and track monthly spending."
)

with st.sidebar:
    st.header("Build stages")
    st.markdown(
        """
        1. Dashboard from sample CSV  
        2. Receipt upload  
        3. Gemini extraction  
        4. Review/edit table  
        5. Save to CSV / Google Sheets  
        6. Monthly summary
        """
    )

    use_demo = st.toggle("Use demo receipt instead of API", value=False)

    data_source = st.selectbox(
        "Dashboard data source",
        ["Google Sheets", "Local CSV"],
    )

    st.divider()
    st.subheader("Admin")

    if st.button("Clear local CSV cache", key="clear_local_csv_cache"):
        for path in ["data/receipts.csv", "data/receipt_items.csv"]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as exc:
                st.warning(f"Could not delete {path}: {exc}")

        st.success("Local CSV cache cleared. Reboot or refresh the app.")

upload_tab, dashboard_tab, data_tab = st.tabs(
    ["Scan receipt", "Dashboard", "Saved data"]
)

with upload_tab:
    st.header("1. Upload a receipt")
    uploaded_file = st.file_uploader(
        "Choose a receipt image",
        type=["png", "jpg", "jpeg", "webp"],
    )

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded receipt", width=350)

    extract_clicked = st.button(
        "Extract receipt data",
        type="primary",
        disabled=(uploaded_file is None and not use_demo),
        key="extract_receipt_data_button",
    )

    if extract_clicked:
        try:
            if use_demo:
                receipt_data = demo_receipt()
            else:
                image_bytes = uploaded_file.getvalue()
                receipt_data = extract_receipt_from_image(
                    image_bytes,
                    uploaded_file.type,
                )

            st.session_state["receipt"] = receipt_data.model_dump()

        except Exception as exc:
            st.error(str(exc))

    if "receipt" in st.session_state:
        receipt = st.session_state["receipt"]

        st.header("2. Review receipt details")

        c1, c2, c3 = st.columns(3)
        receipt["merchant"] = c1.text_input(
            "Merchant",
            receipt.get("merchant", "Unknown Merchant"),
        )
        receipt["date"] = c2.text_input(
            "Date YYYY-MM-DD",
            receipt.get("date") or "",
        )
        receipt["payment_method"] = c3.text_input(
            "Payment method",
            receipt.get("payment_method") or "",
        )

        c4, c5, c6, c7 = st.columns(4)
        receipt["subtotal"] = c4.number_input(
            "Subtotal",
            min_value=0.0,
            value=float(receipt.get("subtotal", 0) or 0),
            step=0.01,
        )
        receipt["tax"] = c5.number_input(
            "Tax",
            min_value=0.0,
            value=float(receipt.get("tax", 0) or 0),
            step=0.01,
        )
        receipt["tip"] = c6.number_input(
            "Tip",
            min_value=0.0,
            value=float(receipt.get("tip", 0) or 0),
            step=0.01,
        )
        receipt["total"] = c7.number_input(
            "Total",
            min_value=0.0,
            value=float(receipt.get("total", 0) or 0),
            step=0.01,
        )

        st.header("3. Review and edit item categories")

        rules = load_rules()
        item_rows = []

        for item in receipt.get("items", []):
            category, summary_group = categorize_item(
                item.get("name", ""),
                item.get("category", "Miscellaneous"),
                rules,
            )

            item_rows.append(
                {
                    "item_name": item.get("name", "Unknown Item"),
                    "item_price": float(item.get("price", 0) or 0),
                    "category": category,
                    "summary_group": summary_group,
                    "confidence": float(item.get("confidence", 0.5) or 0.5),
                    "user_corrected": False,
                }
            )

        items_df = pd.DataFrame(item_rows)

        edited_df = st.data_editor(
            items_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=CATEGORIES,
                ),
                "item_price": st.column_config.NumberColumn(
                    "Price",
                    min_value=0.0,
                    step=0.01,
                    format="$%.2f",
                ),
                "confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    min_value=0.0,
                    max_value=1.0,
                ),
            },
            key="receipt_items_editor",
        )

        warnings = validate_receipt_totals(
            edited_df.to_dict("records"),
            receipt.get("subtotal", 0),
            receipt.get("tax", 0),
            receipt.get("tip", 0),
            receipt.get("total", 0),
        )

        for warning in warnings:
            st.warning(warning)

        save_disabled = edited_df.empty

        if st.button(
            "Save approved receipt",
            disabled=save_disabled,
            key="save_approved_receipt_upload_tab",
        ):
            image_name = uploaded_file.name if uploaded_file else "demo"

            # Save locally to CSV first
            receipt_id = save_receipt(receipt, edited_df, image_name)

            # Build receipt row for Google Sheets
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
                "created_at": pd.Timestamp.now().isoformat(),
            }

            # Build item rows for Google Sheets
            item_rows = []

            item_subtotal = float(edited_df["item_price"].sum() or 0)
            receipt_total = float(receipt.get("total", 0) or 0)

            if item_subtotal > 0 and receipt_total > 0:
                allocation_factor = receipt_total / item_subtotal
            else:
                allocation_factor = 1.0

            for index, item in edited_df.reset_index(drop=True).iterrows():
                item_price = float(item.get("item_price", 0) or 0)
                allocated_price = round(item_price * allocation_factor, 2)


            for index, item in edited_df.reset_index(drop=True).iterrows():
                item_rows.append(
                    {
                        "item_id": f"{receipt_id}-{index + 1}",
                        "receipt_id": receipt_id,
                        "date": receipt.get("date", ""),
                        "merchant": receipt.get("merchant", "Unknown Merchant"),
                        "item_name": item.get("item_name", "Unknown Item"),
                        "item_price": float(item.get("item_price", 0) or 0),
                        "category": item.get("category", "Miscellaneous"),
                        "summary_group": item.get("summary_group", "Other"),
                        "confidence": float(item.get("confidence", 0.5) or 0.5),
                        "user_corrected": bool(item.get("user_corrected", False)),
                        "allocated_price": allocated_price,
                    }
                )

            # Save externally to Google Sheets
            try:
                append_receipt(receipt_row)
                append_receipt_items(item_rows)
                st.success(
                    f"Saved receipt {receipt_id} locally and to Google Sheets. "
                    "Open the Dashboard tab to see updated totals."
                )
            except Exception as exc:
                st.warning(
                    f"Saved receipt {receipt_id} locally, "
                    f"but Google Sheets sync failed: {exc}"
                )

            del st.session_state["receipt"]

with dashboard_tab:
    if data_source == "Google Sheets":
        try:
            sheet_items = pd.DataFrame(read_receipt_items())

            if sheet_items.empty:
                st.info("No Google Sheets receipt items found yet. Save a receipt first.")
            else:
                render_dashboard(sheet_items)

        except Exception as exc:
            st.warning(f"Could not load Google Sheets data: {exc}")
            st.info("Showing local/sample data instead.")
            render_dashboard(load_items(use_sample_if_empty=True))

    else:
        render_dashboard(load_items(use_sample_if_empty=True))

with data_tab:
    if data_source == "Google Sheets":
        try:
            st.header("Saved receipts")
            st.dataframe(pd.DataFrame(read_receipts()), use_container_width=True)

            st.header("Saved receipt items")
            st.dataframe(pd.DataFrame(read_receipt_items()), use_container_width=True)

            st.caption("Showing data from Google Sheets.")

        except Exception as exc:
            st.warning(f"Could not load Google Sheets data: {exc}")
            st.info("Showing local/sample data instead.")

            st.header("Saved receipts")
            st.dataframe(
                load_receipts(use_sample_if_empty=True),
                use_container_width=True,
            )

            st.header("Saved receipt items")
            st.dataframe(
                load_items(use_sample_if_empty=True),
                use_container_width=True,
            )

    else:
        st.header("Saved receipts")
        st.dataframe(
            load_receipts(use_sample_if_empty=True),
            use_container_width=True,
        )

        st.header("Saved receipt items")
        st.dataframe(
            load_items(use_sample_if_empty=True),
            use_container_width=True,
        )

        st.caption("Showing local CSV/sample data.")