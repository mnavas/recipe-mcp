"""Recipe scaling: rescale by yield/factor, percentages, baker's %, ratios.

An "ingredient line" is a dict:
    {"name": "flour", "amount": 500, "unit": "g"}

Weight-based math (percentages, baker's %) converts every line to grams.
Volume units are converted using the ingredient density table, so the line
name must be a known ingredient (or already a weight unit).
"""

from __future__ import annotations

from . import ingredients, units


def _to_grams(line: dict) -> float:
    amount = float(line["amount"])
    unit = line.get("unit", "g")
    if units.is_weight_unit(unit):
        return units.to_grams(amount, unit)
    if units.is_volume_unit(unit):
        return ingredients.volume_to_weight(line["name"], amount, unit, "g")
    raise ValueError(f"Unknown unit {unit!r} for ingredient {line.get('name')!r}")


def total_grams(ingredient_lines: list[dict]) -> float:
    """Total weight of an ingredient list in grams (volumes via density)."""
    return sum(_to_grams(l) for l in ingredient_lines)


def scale_recipe(ingredient_lines: list[dict], *, factor: float | None = None,
                 from_yield: float | None = None,
                 to_yield: float | None = None) -> dict:
    """Multiply every amount by a factor (unit-agnostic, keeps units).

    Provide either `factor`, or both `from_yield` and `to_yield`.
    """
    if factor is None:
        if from_yield is None or to_yield is None:
            raise ValueError("Provide `factor`, or both `from_yield` and `to_yield`.")
        if from_yield == 0:
            raise ValueError("from_yield cannot be zero")
        factor = to_yield / from_yield
    scaled = [
        {"name": l["name"], "amount": round(float(l["amount"]) * factor, 4),
         "unit": l.get("unit", "g")}
        for l in ingredient_lines
    ]
    return {"factor": round(factor, 6), "ingredients": scaled}


def to_percentages(ingredient_lines: list[dict]) -> dict:
    """Express each ingredient as a percentage of total weight."""
    grams = [_to_grams(l) for l in ingredient_lines]
    total = sum(grams)
    if total == 0:
        raise ValueError("Total weight is zero")
    rows = [
        {"name": l["name"], "grams": round(g, 2),
         "percent": round(g / total * 100, 2)}
        for l, g in zip(ingredient_lines, grams)
    ]
    return {"total_grams": round(total, 2), "ingredients": rows}


def bakers_percentages(ingredient_lines: list[dict],
                       flour_keyword: str = "flour") -> dict:
    """Baker's percentages: total flour = 100%, others relative to flour weight."""
    grams = [_to_grams(l) for l in ingredient_lines]
    flour_total = sum(
        g for l, g in zip(ingredient_lines, grams)
        if flour_keyword in l["name"].lower()
    )
    if flour_total == 0:
        raise ValueError(
            f"No flour found (no ingredient name contains {flour_keyword!r}). "
            "Pass a different flour_keyword."
        )
    rows = [
        {"name": l["name"], "grams": round(g, 2),
         "bakers_percent": round(g / flour_total * 100, 2)}
        for l, g in zip(ingredient_lines, grams)
    ]
    return {"flour_grams": round(flour_total, 2), "ingredients": rows}


def apply_bakers_percentages(formula: dict[str, float], flour_grams: float) -> dict:
    """Turn a baker's % formula into weights for a given flour weight.

    `formula` maps ingredient name -> baker's percent (flour should be 100).
    """
    rows = []
    total = 0.0
    for name, pct in formula.items():
        g = flour_grams * float(pct) / 100.0
        total += g
        rows.append({"name": name, "bakers_percent": float(pct), "grams": round(g, 2)})
    return {"flour_grams": flour_grams, "total_grams": round(total, 2), "ingredients": rows}


def solve_ratio(parts: dict[str, float] | list[float], *,
                total: float | None = None,
                known_name: str | None = None,
                known_amount: float | None = None,
                unit: str = "g") -> dict:
    """Scale a ratio (e.g. 3:2:1) to real amounts.

    Provide either `total` (total amount split by the ratio), or a single
    known component (`known_name` + `known_amount`, or `known_amount` with
    a list where the first part is the reference).
    """
    if isinstance(parts, list):
        parts = {f"part_{i + 1}": p for i, p in enumerate(parts)}
    sum_parts = sum(parts.values())
    if sum_parts == 0:
        raise ValueError("Ratio parts sum to zero")

    if total is not None:
        unit_value = total / sum_parts
    elif known_amount is not None:
        ref = known_name if known_name is not None else next(iter(parts))
        if ref not in parts:
            raise ValueError(f"known_name {ref!r} not in ratio {list(parts)}")
        unit_value = known_amount / parts[ref]
    else:
        raise ValueError("Provide `total`, or `known_amount` (+ optional known_name).")

    rows = [
        {"name": name, "parts": p, "amount": round(unit_value * p, 4), "unit": unit}
        for name, p in parts.items()
    ]
    return {"total": round(unit_value * sum_parts, 4), "unit": unit, "ingredients": rows}
