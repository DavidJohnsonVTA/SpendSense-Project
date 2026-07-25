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
- Better OCR fallback
- Category learning from user corrections
- Export monthly report as PDF
