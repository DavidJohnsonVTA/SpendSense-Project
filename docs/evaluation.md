# Evaluation Plan

Use 10 to 20 sample receipts and compare the AI output to manually entered expected results.

Track:

- Merchant accuracy
- Date accuracy
- Total accuracy
- Number of correctly extracted line items
- Category accuracy
- Number of user corrections needed

Example evaluation table:

| receipt | merchant correct | total correct | item extraction accuracy | category accuracy | notes |
|---|---:|---:|---:|---:|---|
| target_01.jpg | 1 | 1 | 0.85 | 0.80 | missed one discount line |

Good next step: create `tests/eval_receipts.csv` and a script that calculates these metrics.
