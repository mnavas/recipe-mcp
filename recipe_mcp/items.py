"""Count ↔ weight table for whole/countable ingredients.

Density (g/ml) answers "how much does a volume weigh"; this answers "how much
does a *piece* weigh" — 1 egg, 1 garlic clove, 1 medium potato — so counts can
be turned into grams when scaling a recipe by weight.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from . import units

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_BUILTIN = _DATA_DIR / "item_weights.json"


def _load_builtin() -> dict[str, dict]:
    with open(_BUILTIN, encoding="utf-8") as fh:
        return json.load(fh)["items"]


# name -> {"grams": float, "note": str}
_ITEMS: dict[str, dict] = _load_builtin()


def _key(name: str) -> str:
    return name.strip().lower()


def load_overrides(path: str | Path) -> int:
    """Merge a user item-weights JSON file (same shapes as the builtin)."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    table = raw.get("items", raw)
    n = 0
    for name, val in table.items():
        if name.startswith("_"):
            continue
        entry = {"grams": float(val)} if isinstance(val, (int, float)) else dict(val)
        _ITEMS[_key(name)] = entry
        n += 1
    return n


def list_items() -> list[dict]:
    """All countable items with the weight of one piece (g) and a note."""
    return [{"name": n, "grams_each": e["grams"], "note": e.get("note", "")}
            for n, e in sorted(_ITEMS.items())]


def _resolve(name: str) -> str | None:
    """Map an ingredient name to a known item key, tolerating modifiers.

    "fresh basil" -> "basil", "red bell pepper" -> "bell pepper".
    """
    key = _key(name)
    if key in _ITEMS:
        return key
    words = set(re.findall(r"[a-z]+", key))
    best = None
    for ik in _ITEMS:
        if all(w in words for w in ik.split()):  # all of the item's words present
            if best is None or len(ik) > len(best):
                best = ik  # prefer the more specific (longer) match
    if best:
        return best
    m = difflib.get_close_matches(key, list(_ITEMS), n=1, cutoff=0.85)
    return m[0] if m else None


def has_item(name: str) -> bool:
    return _resolve(name) is not None


def grams_each(item: str) -> float:
    """Weight of one piece of a countable ingredient, in grams."""
    key = _resolve(item)
    if key is None:
        raise ValueError(f"Unknown countable item: {item!r}.")
    return _ITEMS[key]["grams"]


def count_to_weight(item: str, count: float, weight_unit: str = "g") -> float:
    """Weight of `count` pieces of an item (e.g. 2 eggs -> 100 g)."""
    grams = grams_each(item) * count
    return units.convert_weight(grams, "g", weight_unit)


def weight_to_count(item: str, value: float, weight_unit: str = "g") -> float:
    """How many pieces a given weight is (e.g. 250 g potato -> ~1.5 potatoes)."""
    grams = units.to_grams(value, weight_unit)
    return grams / grams_each(item)
