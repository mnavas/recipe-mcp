import math

import pytest

from recipe_mcp import items, scaling


def test_grams_each():
    assert items.grams_each("egg") == 50
    assert items.grams_each("Garlic") == 5  # case-insensitive


def test_count_to_weight():
    assert math.isclose(items.count_to_weight("egg", 2, "g"), 100.0)
    assert math.isclose(items.count_to_weight("egg", 2, "oz"), 100.0 / 28.349523125)


def test_weight_to_count():
    assert math.isclose(items.weight_to_count("potato", 340, "g"), 2.0)


def test_unknown_item():
    with pytest.raises(ValueError):
        items.grams_each("unicorn")


def test_scaling_counts_toward_weight():
    # 2 eggs (100 g) + 100 g flour = 200 g total
    lines = [{"name": "egg", "amount": 2, "unit": "count"},
             {"name": "all-purpose flour", "amount": 100, "unit": "g"}]
    assert math.isclose(scaling.total_grams(lines), 200.0)
    pct = scaling.to_percentages(lines)
    assert math.isclose(pct["ingredients"][0]["percent"], 50.0)


def test_negligible_units_ignored():
    lines = [{"name": "flour", "amount": 100, "unit": "g"},
             {"name": "black pepper", "amount": 1, "unit": "pinch"}]
    assert math.isclose(scaling.total_grams(lines), 100.0)


def test_scale_to_weight_with_eggs():
    # recipe with eggs scaled to a target total weight
    lines = [{"name": "egg", "amount": 2, "unit": "count"},
             {"name": "all-purpose flour", "amount": 100, "unit": "g"}]
    total = scaling.total_grams(lines)          # 200 g
    factor = 400 / total                         # want 400 g -> x2
    scaled = scaling.scale_recipe(lines, factor=factor)
    assert math.isclose(scaled["ingredients"][0]["amount"], 4.0)  # 4 eggs
