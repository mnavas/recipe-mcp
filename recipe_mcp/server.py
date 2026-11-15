"""MCP server exposing recipe conversion, scaling and the Ollama assistant.

Run with:  python -m recipe_mcp         (stdio transport)
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import assistant, config, ingredients, scaling, units

mcp = MCPServer("recipe-mcp")

# Load config and apply any densities override once at import time.
_CFG = config.load_config()
if _CFG.densities_override:
    try:
        ingredients.load_overrides(_CFG.densities_override)
    except OSError:
        pass


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
