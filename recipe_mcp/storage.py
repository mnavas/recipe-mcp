"""Recipe storage: save, retrieve, search, edit and unit-convert recipes.

Recipes are stored as one JSON file per recipe under ``<data_dir>/recipes/``.
A recipe is a plain dict:

    {
      "id": "sourdough-loaf",
      "name": "Sourdough Loaf",
      "servings": 1,            # base yield (number of servings/loaves/...)
      "yield_unit": "loaf",     # optional label for the yield
      "ingredients": [{"name","amount","unit"}, ...],
      "steps": ["Mix...", "Rest...", ...],
      "notes": "", "tags": [], "source": "",
      "created_at": "...", "updated_at": "..."
    }
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import ingredients as ingredients_mod
from . import units


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "recipe"


def _validate_ingredients(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValueError("ingredients must be a non-empty list of {name, amount, unit}")
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "name" not in it or "amount" not in it:
            raise ValueError(f"ingredient #{i + 1} needs at least name and amount")
        try:
            amount = float(it["amount"])
        except (TypeError, ValueError):
            raise ValueError(f"ingredient {it.get('name')!r} has a non-numeric amount")
        out.append({"name": str(it["name"]), "amount": amount, "unit": str(it.get("unit", "g"))})
    return out


class RecipeStore:
    def __init__(self, data_dir: str | Path):
        self.dir = Path(data_dir) / "recipes"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, recipe_id: str) -> Path:
        return self.dir / f"{recipe_id}.json"

    # -- write ------------------------------------------------------------- #
    def save(self, name: str, ingredients: list[dict], *, steps: list[str] | None = None,
             servings: float = 1, yield_unit: str = "serving", notes: str = "",
             tags: list[str] | None = None, source: str = "",
             recipe_id: str | None = None) -> dict:
        """Create a new recipe or overwrite an existing one (by id)."""
        rid = recipe_id or slugify(name)
        existing = self.get(rid) if self._path(rid).exists() else None
        recipe = {
            "id": rid,
            "name": name,
            "servings": float(servings),
            "yield_unit": yield_unit,
            "ingredients": _validate_ingredients(ingredients),
            "steps": [str(s) for s in (steps or [])],
            "notes": notes,
            "tags": list(tags or []),
            "source": source,
            "created_at": existing["created_at"] if existing else _now(),
            "updated_at": _now(),
        }
        self._write(recipe)
        return recipe

    def update(self, recipe_id: str, patch: dict) -> dict:
        """Merge a partial update into a stored recipe."""
        recipe = self.get(recipe_id)
        if "ingredients" in patch:
            patch = {**patch, "ingredients": _validate_ingredients(patch["ingredients"])}
        if "steps" in patch:
            patch = {**patch, "steps": [str(s) for s in patch["steps"]]}
        recipe.update(patch)
        recipe["id"] = recipe_id
        recipe["updated_at"] = _now()
        self._write(recipe)
        return recipe

    def set_ingredient_unit(self, recipe_id: str, ingredient: str, new_unit: str) -> dict:
        """Convert one ingredient's stored amount to a different unit and save.

        Works within weight, within volume, or across the two using the
        ingredient density table.
        """
        recipe = self.get(recipe_id)
        key = ingredient.strip().lower()
        for line in recipe["ingredients"]:
            if line["name"].strip().lower() == key:
                line["amount"] = round(
                    _convert_amount(line["name"], line["amount"], line["unit"], new_unit), 4)
                line["unit"] = new_unit
                recipe["updated_at"] = _now()
                self._write(recipe)
                return recipe
        raise ValueError(f"{ingredient!r} is not in recipe {recipe_id!r}")

    def delete(self, recipe_id: str) -> bool:
        p = self._path(recipe_id)
        if p.exists():
            p.unlink()
            return True
        return False

    def _write(self, recipe: dict) -> None:
        tmp = self._path(recipe["id"]).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path(recipe["id"]))

    # -- read -------------------------------------------------------------- #
    def get(self, recipe_id: str) -> dict:
        p = self._path(recipe_id)
        if not p.exists():
            raise ValueError(f"No recipe with id {recipe_id!r}. Use list_recipes to see ids.")
        return json.loads(p.read_text(encoding="utf-8"))

    def list(self) -> list[dict]:
        out = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                r = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            out.append({
                "id": r.get("id", p.stem),
                "name": r.get("name", p.stem),
                "servings": r.get("servings", 1),
                "yield_unit": r.get("yield_unit", "serving"),
                "tags": r.get("tags", []),
                "n_ingredients": len(r.get("ingredients", [])),
                "n_steps": len(r.get("steps", [])),
            })
        return out

    def search(self, query: str) -> list[dict]:
        q = query.strip().lower()
        hits = []
        for summary in self.list():
            full = self.get(summary["id"])
            hay = " ".join([
                full.get("name", ""), " ".join(full.get("tags", [])),
                " ".join(i["name"] for i in full.get("ingredients", [])),
                full.get("notes", ""), full.get("source", ""),
            ]).lower()
            if q in hay:
                hits.append(summary)
        return hits


def _convert_amount(ingredient: str, amount: float, from_unit: str, to_unit: str) -> float:
    """Convert an amount between any weight/volume units for a named ingredient."""
    fw, tw = units.is_weight_unit(from_unit), units.is_weight_unit(to_unit)
    fv, tv = units.is_volume_unit(from_unit), units.is_volume_unit(to_unit)
    if fw and tw:
        return units.convert_weight(amount, from_unit, to_unit)
    if fv and tv:
        return units.convert_volume(amount, from_unit, to_unit)
    if fv and tw:  # volume -> weight
        return ingredients_mod.volume_to_weight(ingredient, amount, from_unit, to_unit)
    if fw and tv:  # weight -> volume
        return ingredients_mod.weight_to_volume(ingredient, amount, from_unit, to_unit)
    raise ValueError(f"Cannot convert {from_unit!r} to {to_unit!r}")
