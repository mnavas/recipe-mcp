import math

import pytest

from recipe_mcp import conditions, pans, salt, scaling


# --- pans ------------------------------------------------------------------- #
def test_pan_area_round_vs_square():
    _, area, _ = pans.parse_pan("round:20")
    assert math.isclose(area, math.pi * 100, rel_tol=1e-9)
    _, area2, _ = pans.parse_pan("square:20")
    assert area2 == 400


def test_scale_for_pan():
    r = pans.scale_for_pan("round:20", "round:24")
    assert math.isclose(r["area_factor"], (24 ** 2) / (20 ** 2), rel_tol=1e-9)  # area ∝ d²


def test_pan_rect():
    _, area, label = pans.parse_pan("rect:23x33")
    assert area == 23 * 33 and "23x33" in label


def test_bad_pan():
    with pytest.raises(ValueError):
        pans.parse_pan("hexagon:10")


# --- salt ------------------------------------------------------------------- #
def test_salt_table_to_kosher_diamond():
    # 1 tsp table (1.22) -> Diamond kosher (0.58): ~2.1 tsp
    r = salt.convert_salt(1, "table", "kosher diamond", "tsp")
    assert math.isclose(r["result"], 1.22 / 0.58, rel_tol=1e-6)


def test_salt_weight_unchanged():
    r = salt.convert_salt(10, "table", "flaky", "g")
    assert r["result"] == 10  # equal weight = equal saltiness


# --- gelatin ---------------------------------------------------------------- #
def test_gelatin_sheet_to_powder():
    r = conditions.convert_gelatin(4, "sheet", "powder")
    assert r["grams"] == 8.0
    assert math.isclose(r["powder_tsp"], 8.0 / 3.1, rel_tol=1e-6)


def test_gelatin_powder_to_sheet():
    assert conditions.convert_gelatin(8, "powder", "sheet")["sheets"] == 4.0


# --- pressure cooker -------------------------------------------------------- #
def test_pressure_cooker_sea_level():
    r = conditions.pressure_cooker_time(90, 0)
    assert math.isclose(r["estimate_minutes"], 30.0)


def test_pressure_cooker_altitude_adds_time():
    assert conditions.pressure_cooker_time(90, 2850)["estimate_minutes"] > 30.0


# --- oven calibration ------------------------------------------------------- #
def test_oven_calibration_hot():
    r = conditions.oven_calibration(set_temp=180, actual_temp=195, target_temp=180)
    assert r["measured_offset"] == 15.0 and r["set_dial_to"] == 165.0


# --- humidity --------------------------------------------------------------- #
def test_humidity_bands():
    assert conditions.humidity_tip(30)["band"] == "dry"
    assert conditions.humidity_tip(50)["band"] == "normal"
    assert conditions.humidity_tip(80)["band"] == "humid"


# --- scaling caveats -------------------------------------------------------- #
def test_scaling_caveats_scaleup_mentions_leavening():
    notes = " ".join(scaling.scaling_caveats(3)["caveats"]).lower()
    assert "leavening" in notes
