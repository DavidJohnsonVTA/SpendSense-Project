# Prompt Design

The prompt asks the model to return only JSON because the rest of the app depends on predictable fields.

Important design choices:

- The model receives a receipt image and an extraction prompt.
- The prompt lists allowed categories to reduce category drift.
- The prompt tells the model not to invent unreadable items.
- Python validates the model output with Pydantic.
- The user reviews and edits the result before saving.

This keeps the model as one part of a larger workflow rather than the whole product.
