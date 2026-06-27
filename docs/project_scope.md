# Project Scope

## Problem

Receipts are hard to track manually. Students and everyday users often spend across grocery stores, restaurants, household supplies, school purchases, and miscellaneous categories without a clear monthly summary.

## Solution

SpendSense scans receipt images, extracts structured data using an LLM API, categorizes each item, lets the user review the output, saves the data, and displays a monthly spending dashboard.

## MVP features

1. Upload a receipt image
2. Extract merchant, date, line items, tax, tip, and total
3. Categorize line items
4. Review and edit extracted data
5. Save approved data to CSV
6. View monthly expense dashboard
7. Generate a plain-English monthly spending summary

## Non-goals for V1

- Bank account integration
- Automatic payment syncing
- Tax advice
- Medical or financial advice
- Multi-user authentication
