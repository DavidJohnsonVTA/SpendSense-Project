# SpendSense

SpendSense is an AI-assisted receipt scanner and expense dashboard. It converts receipt images into structured purchase records, lets the user review and correct the extraction, saves approved data, and summarizes monthly spending by category.

## What this project demonstrates

- A workflow that connects receipt images, a multimodal LLM API, structured data storage, and a dashboard
- AI use beyond chatbot interaction: extraction, categorization, validation, review, and summarization
- Human-in-the-loop design so incorrect AI outputs are reviewed before saving
- A realistic personal finance tool for students and everyday users

## Tech stack

- Python
- Streamlit
- Pandas
- Gemini API through the Google GenAI SDK
- CSV storage for version 1

## Setup

```bash
cd spendsense
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your Gemini API key to `.env`:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Run the app:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest
```

## Build stages

### Stage 1: Dashboard from sample data

Run the app and open the Dashboard tab. The app will show sample data until you save your first real receipt.

Goal: prove the monthly summary, category totals, merchant chart, and weekly trend work before adding AI.

### Stage 2: Receipt upload UI

Use the Scan receipt tab to upload a PNG/JPG/WebP receipt image.

Goal: prove the user can upload a receipt and see it in the app.

### Stage 3: AI receipt extraction

Set `GEMINI_API_KEY` in `.env`, upload a receipt, and click Extract receipt data.

Goal: Gemini returns merchant, date, item names, prices, categories, subtotal, tax, tip, and total.

### Stage 4: Human review

Use the editable table to fix incorrect item names, prices, or categories.

Goal: nothing gets saved until the user approves it.

### Stage 5: Save to CSV

Click Save approved receipt. The app writes to:

- `data/receipts.csv`
- `data/receipt_items.csv`

Goal: turn messy receipt data into a reusable dataset.

### Stage 6: Monthly dashboard

Open the Dashboard tab and review monthly spending.

Goal: see totals by category, merchant, total food, groceries, dining out, and trends.

## Future improvements

- Google Sheets sync
- Budget targets by category
- User accounts
- Better OCR fallback
- Category learning from user corrections
- Export monthly report as PDF
