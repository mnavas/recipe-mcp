"""Agentic cooking assistant: the local model can actually CALL the tools.

Unlike `assistant.ask` (a plain chat), this gives the Ollama model the
deterministic recipe-mcp tools via Ollama's tool-calling API, runs any tool the
model asks for, feeds the real result back, and loops until it has an answer.

So "how many ml is 1 g of salt?" is answered by actually running
`volume/weight` conversion, not by the model guessing.

Note: this only works as well as the model's tool-calling. Models like
llama3.1 / qwen2.5 do it well; gemma3n is weak at it and may just reply in
prose (in which case this behaves like the plain assistant).
"""

from __future__ import annotations

import json

from . import ingredients, items, scaling, storage, temperature, units
from .config import DEFAULT_SYSTEM_PROMPT, Config

AGENT_SYSTEM_PROMPT = (
    "You are a practical home-cooking and baking assistant with tools for exact "
    "kitchen math and a recipe library. You are NOT a calculator: whenever a "
    "question needs a unit, weight/volume, count, temperature or scaling "
    "conversion, or a stored recipe, CALL the appropriate tool and use its "
    "result — never compute or guess the number yourself. After the tools "
    "return, give a short, clear answer. Flag food-safety issues."
)


# --- tool implementations (return JSON-serialisable dicts) ------------------ #
def _mk_dispatch(cfg: Config):
    store = storage.RecipeStore(cfg.resolved_data_dir())

    def convert_weight(value, from_unit, to_unit):
        return {"result": units.convert_weight(float(value), from_unit, to_unit), "unit": to_unit}

    def convert_volume(value, from_unit, to_unit):
        return {"result": units.convert_volume(float(value), from_unit, to_unit), "unit": to_unit}

    def convert_temperature(value, from_unit, to_unit):
        return {"result": temperature.convert_temperature(float(value), from_unit, to_unit), "unit": to_unit}

    def oven_temperature(value, unit="C"):
        return temperature.oven(float(value), unit)

    def ingredient_weight_to_volume(ingredient, value, weight_unit="g", volume_unit="ml"):
        return {"result": ingredients.weight_to_volume(ingredient, float(value), weight_unit, volume_unit), "unit": volume_unit}

    def ingredient_volume_to_weight(ingredient, value, volume_unit="ml", weight_unit="g"):
        return {"result": ingredients.volume_to_weight(ingredient, float(value), volume_unit, weight_unit), "unit": weight_unit}

    def count_to_weight(item, count, weight_unit="g"):
        return {"result": items.count_to_weight(item, float(count), weight_unit), "unit": weight_unit}

    def list_recipes():
        return {"recipes": store.list()}

    def get_recipe(recipe_id):
        return store.get(recipe_id)

    def search_recipes(query):
        return {"matches": store.search(query)}

    return {
        "convert_weight": convert_weight,
        "convert_volume": convert_volume,
        "convert_temperature": convert_temperature,
        "oven_temperature": oven_temperature,
        "ingredient_weight_to_volume": ingredient_weight_to_volume,
        "ingredient_volume_to_weight": ingredient_volume_to_weight,
        "count_to_weight": count_to_weight,
        "list_recipes": list_recipes,
        "get_recipe": get_recipe,
        "search_recipes": search_recipes,
    }


def _num(desc):
    return {"type": "number", "description": desc}


def _str(desc):
    return {"type": "string", "description": desc}


TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "convert_weight", "description": "Convert a mass between weight units (mg, g, kg, oz, lb, stone).",
        "parameters": {"type": "object", "required": ["value", "from_unit", "to_unit"],
                       "properties": {"value": _num("amount"), "from_unit": _str("source unit"), "to_unit": _str("target unit")}}}},
    {"type": "function", "function": {
        "name": "convert_volume", "description": "Convert a volume between volume units (ml, l, cup, tbsp, tsp, fl oz).",
        "parameters": {"type": "object", "required": ["value", "from_unit", "to_unit"],
                       "properties": {"value": _num("amount"), "from_unit": _str("source unit"), "to_unit": _str("target unit")}}}},
    {"type": "function", "function": {
        "name": "convert_temperature", "description": "Convert a temperature between C, F and K.",
        "parameters": {"type": "object", "required": ["value", "from_unit", "to_unit"],
                       "properties": {"value": _num("amount"), "from_unit": _str("C, F or K"), "to_unit": _str("C, F or K")}}}},
    {"type": "function", "function": {
        "name": "oven_temperature", "description": "Oven breakdown for a temperature: Celsius, Fahrenheit, gas mark, fan equivalent, description.",
        "parameters": {"type": "object", "required": ["value"],
                       "properties": {"value": _num("temperature"), "unit": _str("C or F (default C)")}}}},
    {"type": "function", "function": {
        "name": "ingredient_weight_to_volume", "description": "Volume a weight of an ingredient occupies, using its density (e.g. 1 g table salt -> ml).",
        "parameters": {"type": "object", "required": ["ingredient", "value"],
                       "properties": {"ingredient": _str("ingredient name"), "value": _num("weight amount"),
                                      "weight_unit": _str("default g"), "volume_unit": _str("default ml")}}}},
    {"type": "function", "function": {
        "name": "ingredient_volume_to_weight", "description": "Weight of a volume of an ingredient, using its density (e.g. 1 tbsp salt -> g).",
        "parameters": {"type": "object", "required": ["ingredient", "value"],
                       "properties": {"ingredient": _str("ingredient name"), "value": _num("volume amount"),
                                      "volume_unit": _str("default ml"), "weight_unit": _str("default g")}}}},
    {"type": "function", "function": {
        "name": "count_to_weight", "description": "Weight of a number of countable items (e.g. 2 eggs -> g).",
        "parameters": {"type": "object", "required": ["item", "count"],
                       "properties": {"item": _str("item name, e.g. egg, garlic"), "count": _num("how many"),
                                      "weight_unit": _str("default g")}}}},
    {"type": "function", "function": {
        "name": "list_recipes", "description": "List the user's stored recipes.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_recipe", "description": "Get a stored recipe (ingredients and steps) by id.",
        "parameters": {"type": "object", "required": ["recipe_id"], "properties": {"recipe_id": _str("recipe id")}}}},
    {"type": "function", "function": {
        "name": "search_recipes", "description": "Search stored recipes by name, tag or ingredient.",
        "parameters": {"type": "object", "required": ["query"], "properties": {"query": _str("search text")}}}},
]


def _extract_tool_calls(message):
    tc = message.get("tool_calls") if isinstance(message, dict) else getattr(message, "tool_calls", None)
    return tc or []


def _call_fields(tc):
    fn = tc["function"] if isinstance(tc, dict) else tc.function
    name = fn["name"] if isinstance(fn, dict) else fn.name
    args = fn["arguments"] if isinstance(fn, dict) else fn.arguments
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    return name, dict(args or {})


def run(cfg: Config, question: str, *, model: str | None = None,
        max_steps: int = 6) -> dict:
    """Answer a question, letting the model call the recipe-mcp tools.

    Returns {"answer": str, "tool_calls": [{"tool", "args", "result"}]}.
    """
    import ollama

    client = ollama.Client(host=cfg.ollama_host)
    dispatch = _mk_dispatch(cfg)
    use_model = model or cfg.model
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    trace: list[dict] = []
    tools_supported = True

    def _chat(msgs, with_tools):
        kw = {"model": use_model, "messages": msgs, "options": {"temperature": cfg.temperature}}
        if with_tools:
            kw["tools"] = TOOL_SCHEMAS
        return client.chat(**kw)

    for _ in range(max_steps):
        try:
            resp = _chat(messages, tools_supported)
        except Exception as exc:  # noqa: BLE001
            if tools_supported and "does not support tools" in str(exc).lower():
                # Model can't tool-call (e.g. gemma3n): answer as a plain chat.
                tools_supported = False
                plain = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                         {"role": "user", "content": question}]
                resp = _chat(plain, False)
                msg = resp["message"] if isinstance(resp, dict) else resp.message
                content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
                return {"answer": content or "", "tool_calls": [], "tools_supported": False}
            raise
        msg = resp["message"] if isinstance(resp, dict) else resp.message
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        calls = _extract_tool_calls(msg)

        if not calls:
            return {"answer": content or "", "tool_calls": trace, "tools_supported": True}

        # record the assistant's tool-call turn, then execute each call
        messages.append({"role": "assistant", "content": content or "", "tool_calls": calls})
        for tc in calls:
            name, args = _call_fields(tc)
            fn = dispatch.get(name)
            if fn is None:
                result = {"error": f"unknown tool {name!r}"}
            else:
                try:
                    result = fn(**args)
                except Exception as exc:  # noqa: BLE001 - surfaced to the model as data
                    result = {"error": str(exc)}
            trace.append({"tool": name, "args": args, "result": result})
            messages.append({"role": "tool", "name": name,
                             "content": json.dumps(result, default=str)})

    # Ran out of steps: ask once more without tools for a final summary.
    resp = _chat(messages, False)
    msg = resp["message"] if isinstance(resp, dict) else resp.message
    content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
    return {"answer": content or "", "tool_calls": trace, "tools_supported": True}
