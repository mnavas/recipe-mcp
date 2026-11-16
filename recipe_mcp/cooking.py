"""Active cooking sessions.

A session is a live cook-along of a stored recipe: the ingredients are scaled to
the batch you actually want, the steps are tracked as done / to-do, and the LLM
can ask what's next and mark progress. Sessions are persisted as JSON under
``<data_dir>/sessions/`` so they survive a server restart.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import scaling
from .storage import RecipeStore


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _resolve_factor(recipe: dict, servings, target_weight_g, factor) -> tuple[float, dict]:
    """Figure out the scale factor and a description of the target."""
    base = recipe.get("servings") or 1
    if factor is not None:
        return float(factor), {"factor": float(factor)}
    if servings is not None:
        if not base:
            raise ValueError("recipe has no base servings to scale from")
        return float(servings) / base, {"servings": float(servings)}
    if target_weight_g is not None:
        current = scaling.total_grams(recipe["ingredients"])
        if current == 0:
            raise ValueError("recipe total weight is zero")
        return float(target_weight_g) / current, {"target_weight_g": float(target_weight_g)}
    return 1.0, {"factor": 1.0}


class CookingStore:
    def __init__(self, data_dir: str | Path, recipes: RecipeStore):
        self.dir = Path(data_dir) / "sessions"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.recipes = recipes

    def _path(self, sid: str) -> Path:
        return self.dir / f"{sid}.json"

    def _write(self, s: dict) -> None:
        tmp = self._path(s["id"]).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path(s["id"]))

    def _scaled_ingredients(self, recipe: dict, factor: float) -> list[dict]:
        return scaling.scale_recipe(recipe["ingredients"], factor=factor)["ingredients"]

    # -- lifecycle --------------------------------------------------------- #
    def start(self, recipe_id: str, *, servings=None, target_weight_g=None,
              factor=None) -> dict:
        recipe = self.recipes.get(recipe_id)
        f, target = _resolve_factor(recipe, servings, target_weight_g, factor)
        sid = f"{recipe_id}-{time.strftime('%Y%m%d-%H%M%S')}"
        session = {
            "id": sid,
            "recipe_id": recipe_id,
            "recipe_name": recipe["name"],
            "status": "active",
            "scale": {"factor": round(f, 6), **target},
            "base_ingredients": recipe["ingredients"],   # unscaled, for re-scaling
            "base_servings": recipe.get("servings", 1),
            "yield_unit": recipe.get("yield_unit", "serving"),
            "ingredients": self._scaled_ingredients(recipe, f),
            "steps": [{"text": t, "done": False} for t in recipe.get("steps", [])],
            "log": [],
            "started_at": _now(),
            "updated_at": _now(),
            "finished_at": None,
        }
        self._write(session)
        return self._view(session)

    def rescale(self, sid: str, *, servings=None, target_weight_g=None, factor=None) -> dict:
        s = self._load(sid)
        recipe_like = {"servings": s["base_servings"], "ingredients": s["base_ingredients"]}
        f, target = _resolve_factor(recipe_like, servings, target_weight_g, factor)
        s["scale"] = {"factor": round(f, 6), **target}
        s["ingredients"] = scaling.scale_recipe(s["base_ingredients"], factor=f)["ingredients"]
        s["updated_at"] = _now()
        self._write(s)
        return self._view(s)

    def complete_step(self, sid: str, step_index: int | None = None) -> dict:
        s = self._load(sid)
        idx = step_index if step_index is not None else self._current_index(s)
        if idx is None:
            raise ValueError("all steps are already done")
        if not (0 <= idx < len(s["steps"])):
            raise ValueError(f"step_index {idx} out of range (0..{len(s['steps']) - 1})")
        s["steps"][idx]["done"] = True
        s["updated_at"] = _now()
        if all(st["done"] for st in s["steps"]) and s["steps"]:
            s["status"] = "done_steps"
        self._write(s)
        return self._view(s)

    def uncomplete_step(self, sid: str, step_index: int) -> dict:
        s = self._load(sid)
        if not (0 <= step_index < len(s["steps"])):
            raise ValueError(f"step_index {step_index} out of range")
        s["steps"][step_index]["done"] = False
        s["status"] = "active"
        s["updated_at"] = _now()
        self._write(s)
        return self._view(s)

    def log(self, sid: str, note: str) -> dict:
        s = self._load(sid)
        s["log"].append({"time": _now(), "note": note})
        s["updated_at"] = _now()
        self._write(s)
        return self._view(s)

    def finish(self, sid: str) -> dict:
        s = self._load(sid)
        s["status"] = "finished"
        s["finished_at"] = _now()
        s["updated_at"] = _now()
        self._write(s)
        return self._view(s)

    def delete(self, sid: str) -> bool:
        p = self._path(sid)
        if p.exists():
            p.unlink()
            return True
        return False

    # -- read -------------------------------------------------------------- #
    def status(self, sid: str) -> dict:
        return self._view(self._load(sid))

    def list(self, include_finished: bool = False) -> list[dict]:
        out = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not include_finished and s.get("status") == "finished":
                continue
            done = sum(1 for st in s.get("steps", []) if st["done"])
            out.append({
                "id": s["id"], "recipe_name": s.get("recipe_name"),
                "status": s.get("status"), "steps_done": done,
                "steps_total": len(s.get("steps", [])),
                "scale": s.get("scale"),
            })
        return out

    # -- helpers ----------------------------------------------------------- #
    def _load(self, sid: str) -> dict:
        p = self._path(sid)
        if not p.exists():
            raise ValueError(f"No cooking session {sid!r}. Use list_cooking_sessions.")
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _current_index(s: dict):
        for i, st in enumerate(s["steps"]):
            if not st["done"]:
                return i
        return None

    def _view(self, s: dict) -> dict:
        """The LLM-facing status: what's done, what's next, scaled ingredients."""
        cur = self._current_index(s)
        done = [{"n": i + 1, "text": st["text"]} for i, st in enumerate(s["steps"]) if st["done"]]
        remaining = [{"n": i + 1, "text": st["text"]}
                     for i, st in enumerate(s["steps"]) if not st["done"]]
        current_step = None
        if cur is not None:
            current_step = {"n": cur + 1, "text": s["steps"][cur]["text"]}
        return {
            "session_id": s["id"],
            "recipe": s["recipe_name"],
            "status": s["status"],
            "scale": s["scale"],
            "ingredients": s["ingredients"],
            "progress": f"{len(done)}/{len(s['steps'])} steps done",
            "current_step": current_step,
            "next_steps": remaining[:3],
            "done_steps": done,
            "log": s.get("log", []),
        }
