import math

import pytest

from recipe_mcp import altitude, yeast


def test_boiling_point_sea_level():
    b = altitude.boiling_point(0, "m")
    assert b["boiling_point_c"] == 100.0


def test_boiling_point_quito():
    b = altitude.boiling_point(2850, "m")   # ~Quito
    assert 89 <= b["boiling_point_c"] <= 91
    assert "pressure cooker" in b["note"]


def test_boiling_point_feet():
    b = altitude.boiling_point(5000, "ft")
    assert b["altitude_m"] == round(5000 / altitude.FT_PER_M)
    assert b["boiling_point_c"] < 100


def test_no_adjust_below_threshold():
    a = altitude.baking_adjustments(500, "m", baking_powder_tsp=2)
    assert a["significant"] is False
    assert a["adjustments"] == []


def test_adjust_reduces_leavening_and_sugar():
    a = altitude.baking_adjustments(
        2000, "m", oven_temp=180, oven_unit="C",
        baking_powder_tsp=2, sugar_cups=1, liquid_cups=1, has_yeast=True)
    assert a["significant"] is True
    items = {x["item"]: x for x in a["adjustments"]}
    assert items["baking powder"]["to"] < 2          # reduced
    assert items["sugar"]["to"] < 1                   # reduced
    assert items["liquid"]["to"] > 1                  # increased
    assert items["oven temperature"]["to"] > 180      # raised
    assert any("Yeast" in n for n in a["notes"])


def test_yeast_fresh_to_instant():
    # 30 g fresh -> ~10 g instant (3:1)
    assert math.isclose(yeast.convert_yeast(30, "fresh", "instant"), 30 * 0.33, rel_tol=1e-9)


def test_yeast_roundtrip():
    g = yeast.convert_yeast(10, "active dry", "fresh")
    back = yeast.convert_yeast(g, "fresh", "active dry")
    assert math.isclose(back, 10, rel_tol=1e-9)


def test_yeast_unknown():
    with pytest.raises(ValueError):
        yeast.convert_yeast(1, "magic", "instant")
