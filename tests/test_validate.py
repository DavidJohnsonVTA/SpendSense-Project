from src.validate import validate_receipt_totals

def test_validate_totals_ok():
    items = [{"price": 4.00}, {"price": 6.00}]
    warnings = validate_receipt_totals(items, subtotal=10.00, tax=1.00, tip=0.00, total=11.00)
    assert warnings == []

def test_validate_totals_warning():
    items = [{"price": 4.00}]
    warnings = validate_receipt_totals(items, subtotal=10.00, tax=1.00, tip=0.00, total=11.00)
    assert warnings
