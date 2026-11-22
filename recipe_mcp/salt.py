"""Salt-type swaps by volume, keeping saltiness the same.

Equal saltiness means equal weight of salt, but salts have very different crystal
densities, so the *volume* changes a lot (1 tsp table salt ≈ 2 tsp Diamond kosher).
"""

from __future__ import annotations

from . import units

# bulk density g/ml for each salt type
SALT_DENSITY = {
    "table": 1.22,
    "fine sea": 1.20,
    "iodized": 1.22,
    "kosher diamond": 0.58,
    "diamond crystal": 0.58,
    "kosher morton": 0.96,
    "morton": 0.96,
    "kosher": 0.58,          # default kosher = Diamond Crystal
    "coarse sea": 1.00,
    "flaky": 0.50,
    "maldon": 0.50,
}


def _resolve(name: str) -> str:
    key = name.strip().lower().replace("-", " ")
    if key in SALT_DENSITY:
        return key
    for k in SALT_DENSITY:
        if key in k or k in key:
            return k
    raise ValueError(f"Unknown salt type {name!r}. Known: {sorted(SALT_DENSITY)}")


def convert_salt(amount: float, from_type: str, to_type: str, unit: str = "tsp") -> dict:
    """Convert a salt amount to a different salt type, keeping saltiness equal.

    With a volume `unit` (tsp, tbsp, ml...) the volume is rescaled by density.
    With a weight unit the amount is unchanged (equal weight = equal saltiness).
    """
    df = SALT_DENSITY[_resolve(from_type)]
    dt = SALT_DENSITY[_resolve(to_type)]
    if units.is_weight_unit(unit):
        return {"from": f"{amount} {unit} {from_type}", "to_type": to_type,
                "result": amount, "unit": unit,
                "note": "same weight = same saltiness"}
    ml_in = units.to_ml(amount, unit)
    grams = ml_in * df
    ml_out = grams / dt
    out = units.convert_volume(ml_out, "ml", unit)
    return {"from": f"{amount} {unit} {from_type}", "to_type": to_type,
            "result": round(out, 3), "unit": unit, "grams_salt": round(grams, 2)}
