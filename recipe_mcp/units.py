"""Weight (mass) and volume unit conversion.

All conversions go through a base unit:
  - weight  -> base is the gram (g)
  - volume  -> base is the millilitre (ml)

Factors are "how many base units in one of this unit".
Spoon/cup units default to US customary; metric and imperial
variants are provided under explicit names.
"""

from __future__ import annotations

# --- weight: grams per unit -------------------------------------------------
WEIGHT_UNITS: dict[str, float] = {
    "mg": 0.001,
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "oz": 28.349523125,
    "ounce": 28.349523125,
    "lb": 453.59237,
    "pound": 453.59237,
    "st": 6350.29318,       # stone
    "stone": 6350.29318,
}

# --- volume: millilitres per unit ------------------------------------------
VOLUME_UNITS: dict[str, float] = {
    "ml": 1.0,
    "milliliter": 1.0,
    "millilitre": 1.0,
    "cl": 10.0,
    "dl": 100.0,
    "l": 1000.0,
    "liter": 1000.0,
    "litre": 1000.0,
    # US customary
    "tsp": 4.92892159375,
    "teaspoon": 4.92892159375,
    "tbsp": 14.78676478125,
    "tablespoon": 14.78676478125,
    "floz": 29.5735295625,
    "fl_oz": 29.5735295625,
    "cup": 236.5882365,
    "cup_us": 236.5882365,
    "pint": 473.176473,
    "pint_us": 473.176473,
    "quart": 946.352946,
    "gallon": 3785.411784,
    # metric
    "cup_metric": 250.0,
    "tbsp_metric": 15.0,
    "tsp_metric": 5.0,
    # imperial (UK)
    "cup_imperial": 284.130625,
    "floz_imperial": 28.4130625,
    "pint_imperial": 568.26125,
}


def _norm(unit: str) -> str:
    return unit.strip().lower().replace(" ", "_")


def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a mass between weight units (e.g. kg -> oz)."""
    f, t = _norm(from_unit), _norm(to_unit)
    if f not in WEIGHT_UNITS:
        raise ValueError(f"Unknown weight unit: {from_unit!r}. Known: {sorted(WEIGHT_UNITS)}")
    if t not in WEIGHT_UNITS:
        raise ValueError(f"Unknown weight unit: {to_unit!r}. Known: {sorted(WEIGHT_UNITS)}")
    return value * WEIGHT_UNITS[f] / WEIGHT_UNITS[t]


def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a volume between volume units (e.g. cup -> ml)."""
    f, t = _norm(from_unit), _norm(to_unit)
    if f not in VOLUME_UNITS:
        raise ValueError(f"Unknown volume unit: {from_unit!r}. Known: {sorted(VOLUME_UNITS)}")
    if t not in VOLUME_UNITS:
        raise ValueError(f"Unknown volume unit: {to_unit!r}. Known: {sorted(VOLUME_UNITS)}")
    return value * VOLUME_UNITS[f] / VOLUME_UNITS[t]


def to_grams(value: float, unit: str) -> float:
    return convert_weight(value, unit, "g")


def to_ml(value: float, unit: str) -> float:
    return convert_volume(value, unit, "ml")


def is_weight_unit(unit: str) -> bool:
    return _norm(unit) in WEIGHT_UNITS


def is_volume_unit(unit: str) -> bool:
    return _norm(unit) in VOLUME_UNITS


def list_units() -> dict[str, list[str]]:
    """Return the canonical unit names grouped by dimension."""
    return {
        "weight": sorted(set(WEIGHT_UNITS)),
        "volume": sorted(set(VOLUME_UNITS)),
    }
