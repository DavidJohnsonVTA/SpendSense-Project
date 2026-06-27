from __future__ import annotations

def money(value) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0

def validate_receipt_totals(items: list[dict], subtotal: float, tax: float, tip: float, total: float, tolerance: float = 2.00) -> list[str]:
    warnings: list[str] = []
    item_sum = round(sum(money(item.get("price", 0)) for item in items), 2)
    subtotal = money(subtotal)
    tax = money(tax)
    tip = money(tip)
    total = money(total)

    if items and subtotal and abs(item_sum - subtotal) > tolerance:
        warnings.append(f"Item sum ${item_sum:.2f} differs from subtotal ${subtotal:.2f} by more than ${tolerance:.2f}.")

    expected_total = round((subtotal or item_sum) + tax + tip, 2)
    if total and abs(expected_total - total) > tolerance:
        warnings.append(f"Expected total ${expected_total:.2f} differs from receipt total ${total:.2f} by more than ${tolerance:.2f}.")

    if not items:
        warnings.append("No line items were extracted. Save only after manually entering items or confirming receipt-level total.")

    return warnings
