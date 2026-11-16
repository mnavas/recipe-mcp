import math

import pytest

from recipe_mcp import temperature as t


def test_c_f():
    assert math.isclose(t.convert_temperature(180, "C", "F"), 356.0)
    assert math.isclose(t.convert_temperature(350, "F", "C"), 176.666667, rel_tol=1e-6)
    assert math.isclose(t.convert_temperature(100, "C", "K"), 373.15)


def test_symbols_and_words():
    assert math.isclose(t.convert_temperature(32, "°F", "°C"), 0.0, abs_tol=1e-9)
    assert math.isclose(t.convert_temperature(0, "celsius", "fahrenheit"), 32.0)


def test_gas_mark():
    assert t.gas_mark_to_celsius(4) == 180
    assert t.gas_mark_to_celsius("1/4") == 110
    assert t.gas_mark_to_celsius("gas 6") == 200


def test_nearest_gas_mark():
    g = t.nearest_gas_mark(180)
    assert g["gas_mark"] == "4" and g["exact"] is True
    assert t.nearest_gas_mark(185)["gas_mark"] in ("4", "5")


def test_fan_adjust():
    assert math.isclose(t.fan_adjust(180, "C", "fan"), 160.0)
    assert math.isclose(t.fan_adjust(160, "C", "conventional"), 180.0)


def test_oven_breakdown():
    o = t.oven(200, "C")
    assert o["fahrenheit"] == 392.0
    assert o["gas_mark"]["gas_mark"] == "6"
    assert o["fan_celsius"] == 180.0
    assert o["description"] in ("hot", "moderately hot")


def test_bad_unit():
    with pytest.raises(ValueError):
        t.convert_temperature(1, "C", "X")
