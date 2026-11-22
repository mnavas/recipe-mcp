"""Convert between yeast types (fresh / active dry / instant).

By weight, relative to fresh (compressed) yeast:
  fresh = 1.0, active dry ≈ 0.40 (2.5:1), instant ≈ 0.33 (3:1).
Sources vary (fresh:dry from 2:1 to 3:1); these are common middle values.
"""

from __future__ import annotations

from . import units

# weight of a type relative to the same leavening power in fresh yeast
_RELATIVE = {
    "fresh": 1.0,
    "cake": 1.0,
    "compressed": 1.0,
    "active dry": 0.40,
    "active": 0.40,
    "dry": 0.40,
    "instant": 0.33,
    "rapid rise": 0.33,
    "bread machine": 0.33,
}


def _norm(t: str) -> str:
    return t.strip().lower().replace("-", " ").replace("_", " ")


def convert_yeast(amount: float, from_type: str, to_type: str, unit: str = "g") -> float:
    """Convert a yeast amount from one type to another (default grams)."""
    f, t = _norm(from_type), _norm(to_type)
    if f not in _RELATIVE:
        raise ValueError(f"Unknown yeast type {from_type!r}. Known: fresh, active dry, instant.")
    if t not in _RELATIVE:
        raise ValueError(f"Unknown yeast type {to_type!r}. Known: fresh, active dry, instant.")
    grams = units.to_grams(amount, unit)
    fresh_equiv = grams / _RELATIVE[f]
    out_grams = fresh_equiv * _RELATIVE[t]
    return units.convert_weight(out_grams, "g", unit)


def types() -> list[dict]:
    seen = {}
    for name, rel in _RELATIVE.items():
        seen.setdefault(rel, name)
    canon = {1.0: "fresh", 0.40: "active dry", 0.33: "instant"}
    return [{"type": canon[r], "weight_vs_fresh": r} for r in (1.0, 0.40, 0.33)]
