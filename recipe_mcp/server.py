"""MCP server exposing recipe conversion, scaling and the Ollama assistant.

Run with:  python -m recipe_mcp         (stdio transport)
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import (assistant, config, cooking, ingredients, items, scaling,
               storage, temperature, units)

mcp = MCPServer("recipe-mcp")

# Load config and apply any override tables once at import time.
_CFG = config.load_config()
if _CFG.densities_override:
    try:
        ingredients.load_overrides(_CFG.densities_override)
    except OSError:
        pass
if _CFG.item_weights_override:
    try:
        items.load_overrides(_CFG.item_weights_override)
    except OSError:
        pass

# Recipe store + cooking sessions, persisted under the data dir.
_RECIPES = storage.RecipeStore(_CFG.resolved_data_dir())
_COOKING = cooking.CookingStore(_CFG.resolved_data_dir(), _RECIPES)


# --------------------------------------------------------------------------- #
# Units
# --------------------------------------------------------------------------- #
@mcp.tool()
def convert_weight(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a mass between weight units (mg, g, kg, oz, lb, stone)."""
    result = units.convert_weight(value, from_unit, to_unit)
    return {"value": value, "from": from_unit, "to": to_unit, "result": result}


@mcp.tool()
def convert_volume(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a volume between volume units (ml, l, cup, tbsp, tsp, fl oz, ...).

    Spoon/cup units are US by default; use *_metric or *_imperial for variants.
    """
    result = units.convert_volume(value, from_unit, to_unit)
    return {"value": value, "from": from_unit, "to": to_unit, "result": result}


@mcp.tool()
def list_units() -> dict:
    """List all supported weight and volume unit names."""
    return units.list_units()


# --------------------------------------------------------------------------- #
# Ingredients: weight <-> volume via density
# --------------------------------------------------------------------------- #
@mcp.tool()
def list_ingredients() -> list[dict]:
    """List known ingredients with their bulk density (g/ml) and notes."""
    return ingredients.list_ingredients()


@mcp.tool()
def ingredient_density(ingredient: str) -> dict:
    """Bulk density (g/ml) of a cooking ingredient, e.g. 'table salt'."""
    d = ingredients.get_density(ingredient)
    return {"ingredient": ingredient, "density_g_per_ml": d}


@mcp.tool()
def weight_to_volume(ingredient: str, value: float, weight_unit: str = "g",
                     volume_unit: str = "ml") -> dict:
    """Volume occupied by a given weight of an ingredient (e.g. 10 g salt -> ml)."""
    result = ingredients.weight_to_volume(ingredient, value, weight_unit, volume_unit)
    return {"ingredient": ingredient, "input": f"{value} {weight_unit}",
            "result": result, "unit": volume_unit}


@mcp.tool()
def volume_to_weight(ingredient: str, value: float, volume_unit: str = "ml",
                     weight_unit: str = "g") -> dict:
    """Weight of a given volume of an ingredient (e.g. 1 tbsp salt -> g)."""
    result = ingredients.volume_to_weight(ingredient, value, volume_unit, weight_unit)
    return {"ingredient": ingredient, "input": f"{value} {volume_unit}",
            "result": result, "unit": weight_unit}


# --------------------------------------------------------------------------- #
# Temperature & oven
# --------------------------------------------------------------------------- #
@mcp.tool()
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a temperature between C, F and K."""
    result = temperature.convert_temperature(value, from_unit, to_unit)
    return {"value": value, "from": from_unit, "to": to_unit, "result": round(result, 2)}


@mcp.tool()
def oven_temperature(value: float, unit: str = "C") -> dict:
    """Full oven breakdown for a (conventional) temperature.

    Returns Celsius, Fahrenheit, the nearest UK gas mark, the fan-oven
    equivalent, and a description (moderate, hot, ...).
    """
    return temperature.oven(value, unit)


@mcp.tool()
def gas_mark_to_temperature(mark: str, unit: str = "C") -> dict:
    """Oven temperature for a UK gas mark (accepts 4, '1/4', '1/2')."""
    c = temperature.gas_mark_to_celsius(mark)
    return {"gas_mark": mark, "result": round(temperature.from_celsius(c, unit), 1),
            "unit": unit.upper().lstrip("°")}


@mcp.tool()
def fan_oven(value: float, unit: str = "C", to: str = "fan") -> dict:
    """Convert between conventional and fan-oven temperatures.

    `to="fan"` lowers by ~20 C (set a fan oven cooler); `to="conventional"`
    raises by ~20 C.
    """
    result = temperature.fan_adjust(value, unit, to)
    return {"value": value, "unit": unit.upper().lstrip("°"), "to": to,
            "result": round(result, 1)}


# --------------------------------------------------------------------------- #
# Countable items: count <-> weight
# --------------------------------------------------------------------------- #
@mcp.tool()
def list_item_weights() -> list[dict]:
    """List countable ingredients and the weight (g) of one piece."""
    return items.list_items()


@mcp.tool()
def item_weight(item: str) -> dict:
    """Weight of one piece of a countable ingredient (e.g. 1 egg ≈ 50 g)."""
    return {"item": item, "grams_each": items.grams_each(item)}


@mcp.tool()
def count_to_weight(item: str, count: float, weight_unit: str = "g") -> dict:
    """Weight of a number of pieces (e.g. 2 eggs -> grams)."""
    result = items.count_to_weight(item, count, weight_unit)
    return {"item": item, "count": count, "result": result, "unit": weight_unit}


@mcp.tool()
def weight_to_count(item: str, value: float, weight_unit: str = "g") -> dict:
    """How many pieces a weight corresponds to (e.g. 250 g potato -> ~1.5)."""
    result = items.weight_to_count(item, value, weight_unit)
    return {"item": item, "input": f"{value} {weight_unit}", "pieces": result}


# --------------------------------------------------------------------------- #
# Scaling / percentages / ratios
# --------------------------------------------------------------------------- #
@mcp.tool()
def scale_recipe(ingredients_list: list[dict[str, Any]],
                 factor: float | None = None,
                 from_yield: float | None = None,
                 to_yield: float | None = None) -> dict:
    """Rescale a recipe. Each item: {name, amount, unit}.

    Provide `factor`, or both `from_yield` and `to_yield` (e.g. 8 -> 12 servings).
    """
    return scaling.scale_recipe(ingredients_list, factor=factor,
                                from_yield=from_yield, to_yield=to_yield)


@mcp.tool()
def recipe_to_percentages(ingredients_list: list[dict[str, Any]]) -> dict:
    """Express each ingredient as a percentage of total weight.

    Each item: {name, amount, unit}. Volume units are converted to weight
    using the ingredient density table, so names must be known ingredients.
    """
    return scaling.to_percentages(ingredients_list)


@mcp.tool()
def bakers_percentages(ingredients_list: list[dict[str, Any]],
                       flour_keyword: str = "flour") -> dict:
    """Compute baker's percentages (total flour = 100%). Each item: {name, amount, unit}."""
    return scaling.bakers_percentages(ingredients_list, flour_keyword)


@mcp.tool()
def apply_bakers_percentages(formula: dict[str, float], flour_grams: float) -> dict:
    """Turn a baker's % formula (name -> percent, flour=100) into weights for a flour weight."""
    return scaling.apply_bakers_percentages(formula, flour_grams)


@mcp.tool()
def solve_ratio(parts: dict[str, float], total: float | None = None,
                known_name: str | None = None, known_amount: float | None = None,
                unit: str = "g") -> dict:
    """Scale a ratio (e.g. {'flour':3,'water':2,'salt':1}) to amounts.

    Provide `total`, or a known component (`known_name` + `known_amount`).
    """
    return scaling.solve_ratio(parts, total=total, known_name=known_name,
                               known_amount=known_amount, unit=unit)


# --------------------------------------------------------------------------- #
# Recipe storage
# --------------------------------------------------------------------------- #
@mcp.tool()
def save_recipe(name: str, ingredients_list: list[dict[str, Any]],
                steps: list[str] | None = None, servings: float = 1,
                yield_unit: str = "serving", notes: str = "",
                tags: list[str] | None = None, source: str = "",
                recipe_id: str | None = None) -> dict:
    """Save a recipe (or overwrite one with the same id).

    Each ingredient: {name, amount, unit}. `servings` is the base yield used
    later for scaling. Returns the stored recipe including its `id`.
    """
    return _RECIPES.save(name, ingredients_list, steps=steps, servings=servings,
                         yield_unit=yield_unit, notes=notes, tags=tags,
                         source=source, recipe_id=recipe_id)


@mcp.tool()
def get_recipe(recipe_id: str) -> dict:
    """Retrieve a stored recipe by id (ingredients, steps, notes)."""
    return _RECIPES.get(recipe_id)


@mcp.tool()
def list_recipes() -> list[dict]:
    """List stored recipes (id, name, servings, tags, counts)."""
    return _RECIPES.list()


@mcp.tool()
def search_recipes(query: str) -> list[dict]:
    """Find stored recipes by name, tag, ingredient, note or source."""
    return _RECIPES.search(query)


@mcp.tool()
def delete_recipe(recipe_id: str) -> dict:
    """Delete a stored recipe."""
    return {"deleted": _RECIPES.delete(recipe_id), "recipe_id": recipe_id}


@mcp.tool()
def update_recipe(recipe_id: str, patch: dict[str, Any]) -> dict:
    """Patch fields of a stored recipe (name, ingredients, steps, notes, tags...)."""
    return _RECIPES.update(recipe_id, patch)


@mcp.tool()
def set_recipe_ingredient_unit(recipe_id: str, ingredient: str, new_unit: str) -> dict:
    """Change the stored unit of one ingredient, converting its amount.

    Handles weight↔weight, volume↔volume, and weight↔volume (via density).
    """
    return _RECIPES.set_ingredient_unit(recipe_id, ingredient, new_unit)


@mcp.tool()
def scale_stored_recipe(recipe_id: str, servings: float | None = None,
                        target_weight_g: float | None = None,
                        factor: float | None = None,
                        save_as: str | None = None) -> dict:
    """Scale a stored recipe to a target servings, total weight, or factor.

    Returns the scaled ingredients. If `save_as` is given, stores the result as
    a new recipe with that name.
    """
    recipe = _RECIPES.get(recipe_id)
    f, target = cooking._resolve_factor(recipe, servings, target_weight_g, factor)
    scaled = scaling.scale_recipe(recipe["ingredients"], factor=f)
    result = {"recipe_id": recipe_id, "name": recipe["name"], "scale": {"factor": round(f, 6), **target},
              "ingredients": scaled["ingredients"], "steps": recipe.get("steps", [])}
    if save_as:
        saved = _RECIPES.save(save_as, scaled["ingredients"], steps=recipe.get("steps"),
                              servings=target.get("servings", recipe.get("servings", 1)),
                              yield_unit=recipe.get("yield_unit", "serving"),
                              notes=f"Scaled from {recipe['name']} (×{round(f, 3)})",
                              tags=recipe.get("tags"), source=recipe.get("source", ""))
        result["saved_recipe_id"] = saved["id"]
    return result


# --------------------------------------------------------------------------- #
# Cooking sessions (cook-along)
# --------------------------------------------------------------------------- #
@mcp.tool()
def start_cooking(recipe_id: str, servings: float | None = None,
                  target_weight_g: float | None = None,
                  factor: float | None = None) -> dict:
    """Begin cooking a stored recipe, scaled to your batch.

    Scales ingredients to `servings`, `target_weight_g`, or `factor` (default 1×),
    initialises step tracking, and returns the first step plus scaled ingredients.
    """
    return _COOKING.start(recipe_id, servings=servings,
                          target_weight_g=target_weight_g, factor=factor)


@mcp.tool()
def cooking_status(session_id: str) -> dict:
    """Current state of a cook: scaled ingredients, what's done, and what's next."""
    return _COOKING.status(session_id)


@mcp.tool()
def complete_step(session_id: str, step_index: int | None = None) -> dict:
    """Mark a step done (defaults to the current step) and return what's next."""
    return _COOKING.complete_step(session_id, step_index)


@mcp.tool()
def uncomplete_step(session_id: str, step_index: int) -> dict:
    """Re-open a previously completed step (0-based index)."""
    return _COOKING.uncomplete_step(session_id, step_index)


@mcp.tool()
def rescale_cooking(session_id: str, servings: float | None = None,
                    target_weight_g: float | None = None,
                    factor: float | None = None) -> dict:
    """Re-scale an in-progress cook (e.g. decide to make more) keeping step progress."""
    return _COOKING.rescale(session_id, servings=servings,
                            target_weight_g=target_weight_g, factor=factor)


@mcp.tool()
def log_cooking(session_id: str, note: str) -> dict:
    """Add a timestamped note to a cook (e.g. 'dough felt dry, added 10 g water')."""
    return _COOKING.log(session_id, note)


@mcp.tool()
def finish_cooking(session_id: str) -> dict:
    """Mark a cooking session finished."""
    return _COOKING.finish(session_id)


@mcp.tool()
def list_cooking_sessions(include_finished: bool = False) -> list[dict]:
    """List cooking sessions and their progress."""
    return _COOKING.list(include_finished)


# --------------------------------------------------------------------------- #
# Ollama cooking assistant
# --------------------------------------------------------------------------- #
@mcp.tool()
def cooking_assistant(question: str, context: str | None = None,
                      model: str | None = None,
                      temperature: float | None = None) -> dict:
    """Ask the local Ollama cooking assistant a question.

    Optionally override the model or temperature for this one call.
    """
    answer = assistant.ask(_CFG, question, context=context, model=model,
                           temperature=temperature)
    return {"model": model or _CFG.model, "answer": answer}


@mcp.tool()
def assistant_models() -> dict:
    """List models installed in the local Ollama instance."""
    return {"host": _CFG.ollama_host, "models": assistant.list_models(_CFG)}


@mcp.tool()
def assistant_health() -> dict:
    """Check that Ollama is reachable and the configured model is installed."""
    return assistant.health(_CFG)


@mcp.tool()
def get_config() -> dict:
    """Show the current server configuration (model, host, temperature, ...)."""
    from dataclasses import asdict
    return asdict(_CFG)


@mcp.tool()
def set_config(model: str | None = None, ollama_host: str | None = None,
               temperature: float | None = None,
               system_prompt: str | None = None, persist: bool = False) -> dict:
    """Update assistant settings for this session (optionally persist to config.json)."""
    if model is not None:
        _CFG.model = model
    if ollama_host is not None:
        _CFG.ollama_host = ollama_host
    if temperature is not None:
        _CFG.temperature = temperature
    if system_prompt is not None:
        _CFG.system_prompt = system_prompt
    saved = config.save_config(_CFG) if persist else None
    from dataclasses import asdict
    return {"config": asdict(_CFG), "saved_to": saved}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
