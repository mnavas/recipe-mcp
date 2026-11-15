import math

import pytest

from recipe_mcp import units


def test_weight_roundtrip():
    assert math.isclose(units.convert_weight(1, "kg", "g"), 1000.0)
    assert math.isclose(units.convert_weight(16, "oz", "lb"), 1.0, rel_tol=1e-9)
    assert math.isclose(units.convert_weight(1, "lb", "oz"), 16.0, rel_tol=1e-9)


def test_weight_oz_to_g():
    assert math.isclose(units.convert_weight(1, "oz", "g"), 28.349523125)


def test_volume_cup_to_ml():
    assert math.isclose(units.convert_volume(1, "cup", "ml"), 236.5882365)
    assert math.isclose(units.convert_volume(3, "tsp", "tbsp"), 1.0, rel_tol=1e-9)


def test_case_and_space_insensitive():
    assert math.isclose(units.convert_volume(1, "Fl Oz", "ml"), 29.5735295625)


def test_unknown_unit():
    with pytest.raises(ValueError):
        units.convert_weight(1, "g", "furlong")


def test_list_units():
    u = units.list_units()
    assert "g" in u["weight"] and "ml" in u["volume"]
