"""High-altitude cooking and baking helpers.

At altitude, lower air pressure means water boils cooler (slower boiling/
simmering) and leavening gases expand more (doughs over-rise, then collapse),
while faster evaporation dries batters out. These helpers give the standard
adjustments. Rules of thumb vary by source and recipe — change one thing at a
time and test.
"""

from __future__ import annotations

FT_PER_M = 3.280839895


def to_metres(altitude: float, unit: str = "m") -> float:
    u = unit.strip().lower()
    if u in ("m", "metre", "meter", "metres", "meters"):
        return altitude
    if u in ("ft", "foot", "feet"):
        return altitude / FT_PER_M
    raise ValueError("altitude unit must be 'm' or 'ft'")


def boiling_point(altitude: float = 0, unit: str = "m") -> dict:
    """Approximate boiling point of water at an altitude.

    Uses ~1 C drop per 285 m (≈ 1 F per 500 ft).
    """
    m = max(0.0, to_metres(altitude, unit))
    c = 100.0 - m / 285.0
    f = c * 9 / 5 + 32
    note = "near sea level — normal boiling."
    if m >= 1500:
        note = ("boils well below 100 C — boiled and simmered foods (eggs, pasta, "
                "beans, stews) take noticeably longer; a pressure cooker restores "
                "~100 C+ and cuts the time.")
    elif m >= 600:
        note = "slightly cooler boil — boiled/simmered foods take a little longer."
    return {"altitude_m": round(m), "altitude_ft": round(m * FT_PER_M),
            "boiling_point_c": round(c, 1), "boiling_point_f": round(f, 1), "note": note}


def _bracket(alt_ft: float):
    """Return (label, oven_add_F, leaven_reduce_frac, sugar_tbsp_per_cup, liquid_tbsp_per_cup)."""
    if alt_ft < 3000:
        return None
    if alt_ft < 5000:
        return ("3,000-5,000 ft", 15, 0.125, 1.0, 1.5)
    if alt_ft < 6500:
        return ("5,000-6,500 ft", 20, 0.1875, 2.0, 2.5)
    return ("6,500+ ft", 25, 0.25, 3.0, 3.5)


def baking_adjustments(altitude: float = 0, unit: str = "m", *,
                       oven_temp: float | None = None, oven_unit: str = "C",
                       baking_powder_tsp: float | None = None,
                       baking_soda_tsp: float | None = None,
                       sugar_cups: float | None = None,
                       liquid_cups: float | None = None,
                       has_yeast: bool = False) -> dict:
    """Recommend high-altitude baking adjustments for a recipe.

    Pass whichever amounts you have; each is adjusted. Leavening in teaspoons,
    sugar and liquid in cups, oven temperature in C (or F via oven_unit).
    """
    m = max(0.0, to_metres(altitude, unit))
    alt_ft = m * FT_PER_M
    boil = boiling_point(m, "m")
    br = _bracket(alt_ft)
    if br is None:
        return {"altitude_m": round(m), "altitude_ft": round(alt_ft),
                "significant": False, "boiling_point_c": boil["boiling_point_c"],
                "adjustments": [],
                "notes": ["Below ~3,000 ft / 915 m: no significant baking adjustment needed."]}

    label, oven_add_f, leaven_frac, sugar_tbsp, liquid_tbsp = br
    adjustments = []

    if oven_temp is not None:
        add = oven_add_f if oven_unit.strip().upper().lstrip("°") == "F" else oven_add_f * 5 / 9
        adjustments.append({"item": "oven temperature",
                            "from": round(oven_temp, 1), "to": round(oven_temp + add, 1),
                            "unit": oven_unit.upper().lstrip("°"),
                            "note": f"raise ~{round(add,1)} deg (hotter set compensates for the lower boil)"})

    for name, amt in (("baking powder", baking_powder_tsp), ("baking soda", baking_soda_tsp)):
        if amt is not None:
            adjustments.append({"item": name, "from": amt, "to": round(amt * (1 - leaven_frac), 3),
                                "unit": "tsp", "note": f"reduce ~{round(leaven_frac*100)}% (gases over-expand at altitude)"})

    if sugar_cups is not None:
        remove = sugar_tbsp * sugar_cups
        adjustments.append({"item": "sugar", "from": sugar_cups,
                            "to": round(sugar_cups - remove / 16, 3), "unit": "cup",
                            "note": f"reduce ~{sugar_tbsp:g} tbsp per cup (strengthens the crumb)"})

    if liquid_cups is not None:
        add = liquid_tbsp * liquid_cups
        adjustments.append({"item": "liquid", "from": liquid_cups,
                            "to": round(liquid_cups + add / 16, 3), "unit": "cup",
                            "note": f"add ~{liquid_tbsp:g} tbsp per cup (counters faster evaporation)"})

    notes = [
        f"Altitude band: {label}.",
        "Check for doneness a few minutes early — higher heat bakes faster.",
        "Grease pans well and don't overfill; batters rise more and can overflow.",
    ]
    if has_yeast:
        notes.append("Yeast doughs rise faster: cut yeast ~25%, or do a shorter rise / "
                     "an extra punch-down. Don't over-proof.")
    notes.append("These are starting points; change one variable at a time and test.")

    return {"altitude_m": round(m), "altitude_ft": round(alt_ft), "significant": True,
            "band": label, "boiling_point_c": boil["boiling_point_c"],
            "adjustments": adjustments, "notes": notes}
