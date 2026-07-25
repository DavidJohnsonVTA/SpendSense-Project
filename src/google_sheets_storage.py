from __future__ import annotations

import os
from typing import Dict, List

import gspread
from google.oauth2.service_account import Credentials


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_client():
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not credentials_path:
        raise RuntimeError(
            "Missing GOOGLE_APPLICATION_CREDENTIALS. "
            "Set it to the path of your Google service account JSON file."
        )

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def _open_spreadsheet():
    spreadsheet_id = os.getenv("SPENDSENSE_SHEET_ID")

    if not spreadsheet_id:
        raise RuntimeError(
            "Missing SPENDSENSE_SHEET_ID. "
            "Set it to your Google Sheet ID."
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