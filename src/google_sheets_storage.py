from __future__ import annotations

import os
from typing import Dict, List

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_secret(name: str, default: str | None = None) -> str | None:
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def _get_client():
    """
    Local:
      Uses GOOGLE_APPLICATION_CREDENTIALS from .env.

    Streamlit Cloud:
      Uses [gcp_service_account] from Streamlit Secrets.
    """
    try:
        if "gcp_service_account" in st.secrets:
            service_account_info = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES,
            )
            return gspread.authorize(credentials)
    except Exception:
        pass

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not credentials_path:
        raise RuntimeError(
            "Missing Google credentials. Locally, set GOOGLE_APPLICATION_CREDENTIALS "
            "in .env. On Streamlit Cloud, add [gcp_service_account] to Secrets."
        )

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def _open_spreadsheet():
    spreadsheet_id = _get_secret("SPENDSENSE_SHEET_ID")

    if not spreadsheet_id:
        raise RuntimeError(
            "Missing SPENDSENSE_SHEET_ID. Add it to .env locally or Streamlit Secrets."
        )

    client = _get_client()
    return client.open_by_key(spreadsheet_id)


def append_receipt(receipt: Dict):
    sheet = _open_spreadsheet()
    worksheet = sheet.worksheet("receipts")

    headers = worksheet.row_values(1)
    row = [receipt.get(header, "") for header in headers]

    worksheet.append_row(row, value_input_option="USER_ENTERED")


def append_receipt_items(items: List[Dict]):
    if not items:
        return

    sheet = _open_spreadsheet()
    worksheet = sheet.worksheet("receipt_items")

    headers = worksheet.row_values(1)
    rows = []

    for item in items:
        rows.append([item.get(header, "") for header in headers])

    worksheet.append_rows(rows, value_input_option="USER_ENTERED")


def read_receipts() -> List[Dict]:
    sheet = _open_spreadsheet()
    worksheet = sheet.worksheet("receipts")
    return worksheet.get_all_records()


def read_receipt_items() -> List[Dict]:
    sheet = _open_spreadsheet()
    worksheet = sheet.worksheet("receipt_items")
    return worksheet.get_all_records()