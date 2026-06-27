# Runbook

## Start the app

```bash
streamlit run app.py
```

## Add API key

Copy `.env.example` to `.env` and add your Gemini key.

## Reset saved data

Delete these files:

```bash
data/receipts.csv
data/receipt_items.csv
```

The app will recreate them.

## Common issues

### Missing GEMINI_API_KEY

Add the key to `.env` and restart Streamlit.

### Model returns bad JSON

Try a clearer receipt image. The app uses JSON mode, but receipt images with bad lighting or cropped totals can still fail.

### Totals do not match

This can happen because of tax, tip, discounts, unreadable receipt lines, or OCR/model mistakes. Review the table before saving.
