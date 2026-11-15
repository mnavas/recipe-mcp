"""Ingredient density table and weight <-> volume conversion.

Density is stored in g/ml (bulk / scooped density for cooking).
A user override file can add or replace entries at runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import units

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_BUILTIN = _DATA_DIR / "densities.json"


def _load_builtin() -> dict[str, dict]:
    with open(_BUILTIN, encoding="utf-8") as fh:
        return json.load(fh)["ingredients"]


# name -> {"density": g/ml, "note": str}
_DENSITIES: dict[str, dict] = _load_builtin()


def _key(name: str) -> str:
    return name.strip().lower()


def load_overrides(path: str | Path) -> int:
    """Merge a user densities JSON file.

    Accepts either {"ingredients": {...}} or a flat {name: density} /
    {name: {"density": x}} mapping. Returns the number of entries merged.
    """
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    table = raw.get("ingredients", raw)
    n = 0
    for name, val in table.items():
        if name.startswith("_"):
            continue
        entry = {"density": float(val)} if isinstance(val, (int, float)) else dict(val)
        _DENSITIES[_key(name)] = entry
        n += 1
    return n


def list_ingredients() -> list[dict]:
    """All known ingredients with density (g/ml) and note."""
    out = []
    for name, e in sorted(_DENSITIES.items()):
        out.append({"name": name, "density_g_per_ml": e["density"], "note": e.get("note", "")})
    return out


def get_density(ingredient: str) -> float:
    """Density of an ingredient in g/ml. Raises if unknown."""
    key = _key(ingredient)
    if key not in _DENSITIES:
        hint = _closest(key)
        msg = f"Unknown ingredient: {ingredient!r}."
        if hint:
            msg += f" Did you mean {hint!r}?"
        raise ValueError(msg)
    return _DENSITIES[key]["density"]


def _closest(key: str) -> str | None:
    for name in _DENSITIES:
        if key in name or name in key:
            return name
    import difflib
    m = difflib.get_close_matches(key, list(_DENSITIES), n=1, cutoff=0.6)
    return m[0] if m else None


def weight_to_volume(ingredient: str, value: float, weight_unit: str = "g",
                     volume_unit: str = "ml") -> float:
    """How much volume a given weight of an ingredient occupies.

    volume_ml = grams / density(g/ml)
    """
    grams = units.to_grams(value, weight_unit)
    ml = grams / get_density(ingredient)
    return units.convert_volume(ml, "ml", volume_unit)


def volume_to_weight(ingredient: str, value: float, volume_unit: str = "ml",
                     weight_unit: str = "g") -> float:
    """How much a given volume of an ingredient weighs.

    grams = ml * density(g/ml)
    """
    ml = units.to_ml(value, volume_unit)
    grams = ml * get_density(ingredient)
    return units.convert_weight(grams, "g", weight_unit)
