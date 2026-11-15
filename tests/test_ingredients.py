import math

import pytest

from recipe_mcp import ingredients


def test_salt_density():
    assert ingredients.get_density("table salt") == 1.22
    assert ingredients.get_density("Table Salt") == 1.22  # case-insensitive


def test_weight_to_volume_salt():
    # 1.22 g/ml  =>  1 g salt occupies ~0.82 ml
    ml = ingredients.weight_to_volume("table salt", 1, "g", "ml")
    assert math.isclose(ml, 1 / 1.22, rel_tol=1e-9)


def test_volume_to_weight_salt():
    # 1 ml salt weighs 1.22 g
    g = ingredients.volume_to_weight("table salt", 1, "ml", "g")
    assert math.isclose(g, 1.22, rel_tol=1e-9)


def test_roundtrip():
    g = ingredients.volume_to_weight("all-purpose flour", 1, "cup", "g")
    back = ingredients.weight_to_volume("all-purpose flour", g, "g", "cup")
    assert math.isclose(back, 1.0, rel_tol=1e-9)


def test_unknown_ingredient_hint():
    with pytest.raises(ValueError):
        ingredients.get_density("unobtainium")
