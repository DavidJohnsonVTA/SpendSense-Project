from src.categorize import categorize_item

def test_rule_categorizes_household():
    category, group = categorize_item("Laundry Detergent")
    assert category == "Household"
    assert group == "Essentials"

def test_unknown_keeps_misc():
    category, group = categorize_item("Unclear Item", "Miscellaneous")
    assert category == "Miscellaneous"
    assert group == "Miscellaneous"
