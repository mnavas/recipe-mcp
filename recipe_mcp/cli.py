"""A small human-facing command line for recipe-mcp.

The MCP server (``python -m recipe_mcp``) is meant to be driven by an AI client.
This CLI lets you use the same conversions directly from a terminal:

    python -m recipe_mcp.cli convert 2 cup ml
    python -m recipe_mcp.cli convert 1 lb g
    python -m recipe_mcp.cli vtow "table salt" 1 tbsp g
    python -m recipe_mcp.cli wtov "all-purpose flour" 125 g cup
    python -m recipe_mcp.cli ingredients
    python -m recipe_mcp.cli ask "why weigh flour instead of cups?"
"""

from __future__ import annotations

import argparse
import sys

from . import ingredients, units


def _convert(args) -> int:
    f, t = args.from_unit, args.to_unit
    if units.is_weight_unit(f) and units.is_weight_unit(t):
        out = units.convert_weight(args.value, f, t)
    elif units.is_volume_unit(f) and units.is_volume_unit(t):
        out = units.convert_volume(args.value, f, t)
    else:
        print(
            f"error: {f!r} and {t!r} are not the same kind of unit.\n"
            "Use `vtow`/`wtov` to convert between weight and volume for an ingredient.",
            file=sys.stderr,
        )
        return 2
    print(f"{args.value} {f} = {out:.4g} {t}")
    return 0


def _vtow(args) -> int:
    g = ingredients.volume_to_weight(args.ingredient, args.value, args.volume_unit, args.weight_unit)
    print(f"{args.value} {args.volume_unit} {args.ingredient} = {g:.4g} {args.weight_unit}")
    return 0


def _wtov(args) -> int:
    v = ingredients.weight_to_volume(args.ingredient, args.value, args.weight_unit, args.volume_unit)
    print(f"{args.value} {args.weight_unit} {args.ingredient} = {v:.4g} {args.volume_unit}")
    return 0


def _ingredients(_args) -> int:
    for row in ingredients.list_ingredients():
        note = f"  — {row['note']}" if row["note"] else ""
        print(f"{row['name']:<22} {row['density_g_per_ml']:>6} g/ml{note}")
    return 0


def _oven(args) -> int:
    from . import temperature
    o = temperature.oven(args.value, args.unit)
    g = o["gas_mark"]
    print(f"{o['input']}  =  {o['celsius']}C / {o['fahrenheit']}F  "
          f"· gas mark {g['gas_mark']}  · fan {o['fan_celsius']}C  ({o['description']})")
    return 0


def _store():
    from . import config, storage
    return storage.RecipeStore(config.load_config().resolved_data_dir())


def _recipes(_args) -> int:
    rows = _store().list()
    if not rows:
        print("No recipes stored yet. Import one with `import <file.json>` "
              "or save via an MCP client.")
        return 0
    for r in rows:
        print(f"{r['id']:<28} {r['name']:<28} "
              f"{r['servings']:g} {r['yield_unit']}  "
              f"· {r['n_ingredients']} ingredients, {r['n_steps']} steps")
    return 0


def _show(args) -> int:
    r = _store().get(args.recipe_id)
    print(f"# {r['name']}  ({r['servings']:g} {r['yield_unit']})")
    if r.get("tags"):
        print("tags:", ", ".join(r["tags"]))
    print("\nIngredients:")
    for i in r["ingredients"]:
        print(f"  - {i['amount']:g} {i['unit']} {i['name']}")
    if r.get("steps"):
        print("\nSteps:")
        for n, s in enumerate(r["steps"], 1):
            print(f"  {n}. {s}")
    if r.get("notes"):
        print("\nNotes:", r["notes"])
    return 0


def _import(args) -> int:
    import json
    store = _store()
    for path in args.files:
        data = json.loads(open(path, encoding="utf-8").read())
        r = store.save(
            data["name"], data["ingredients"], steps=data.get("steps"),
            servings=data.get("servings", 1), yield_unit=data.get("yield_unit", "serving"),
            notes=data.get("notes", ""), tags=data.get("tags"), source=data.get("source", ""),
            recipe_id=data.get("id"))
        print(f"saved recipe '{r['id']}'")
    return 0


def _ask(args) -> int:
    from . import assistant, config
    try:
        print(assistant.ask(config.load_config(), " ".join(args.question)))
    except Exception as exc:  # noqa: BLE001
        print(f"assistant error: {exc}\n(is Ollama running? `ollama serve`)", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="recipe_mcp.cli", description="recipe-mcp command line")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="convert within weight or within volume")
    c.add_argument("value", type=float)
    c.add_argument("from_unit")
    c.add_argument("to_unit")
    c.set_defaults(func=_convert)

    v = sub.add_parser("vtow", help="volume -> weight for an ingredient")
    v.add_argument("ingredient")
    v.add_argument("value", type=float)
    v.add_argument("volume_unit")
    v.add_argument("weight_unit", nargs="?", default="g")
    v.set_defaults(func=_vtow)

    w = sub.add_parser("wtov", help="weight -> volume for an ingredient")
    w.add_argument("ingredient")
    w.add_argument("value", type=float)
    w.add_argument("weight_unit")
    w.add_argument("volume_unit", nargs="?", default="ml")
    w.set_defaults(func=_wtov)

    sub.add_parser("ingredients", help="list known ingredients and densities").set_defaults(func=_ingredients)

    ov = sub.add_parser("oven", help="oven breakdown: C/F/gas mark/fan")
    ov.add_argument("value", type=float)
    ov.add_argument("unit", nargs="?", default="C")
    ov.set_defaults(func=_oven)

    sub.add_parser("recipes", help="list stored recipes").set_defaults(func=_recipes)

    sh = sub.add_parser("show", help="show a stored recipe")
    sh.add_argument("recipe_id")
    sh.set_defaults(func=_show)

    im = sub.add_parser("import", help="import recipe(s) from JSON file(s)")
    im.add_argument("files", nargs="+")
    im.set_defaults(func=_import)

    a = sub.add_parser("ask", help="ask the local Ollama cooking assistant")
    a.add_argument("question", nargs="+")
    a.set_defaults(func=_ask)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
