# recipe-mcp — worked examples

Each tool is shown as a call with representative arguments and the shape of the
result. In an MCP client you invoke these by name; the examples below mirror the
Python signatures in [`recipe_mcp/server.py`](../recipe_mcp/server.py).

An **ingredient line** (used by the scaling tools) is always:

```json
{ "name": "flour", "amount": 500, "unit": "g" }
```

---

## Units

### `convert_weight(value, from_unit, to_unit)`
```python
convert_weight(2, "kg", "oz")
# → {"value": 2, "from": "kg", "to": "oz", "result": 70.548...}
```
Units: `mg g kg oz lb stone` (plus aliases like `gram`, `pound`). Case- and
space-insensitive.

### `convert_volume(value, from_unit, to_unit)`
```python
convert_volume(1, "cup", "ml")      # → 236.588
convert_volume(3, "tsp", "tbsp")    # → 1.0
```
Spoon/cup units are **US by default**. Use suffixes for variants:
`cup_metric` (250 ml), `tbsp_metric` (15 ml), `cup_imperial` (284.13 ml),
`floz_imperial`, `pint_imperial`.

### `list_units()`
Returns `{"weight": [...], "volume": [...]}` with every accepted name.

---

## Ingredient weight ⇄ volume

These use the bulk-density table in [`data/densities.json`](../data/densities.json)
(densities in **g/ml**).

### `ingredient_density(ingredient)`
```python
ingredient_density("table salt")
# → {"ingredient": "table salt", "density_g_per_ml": 1.22}
```

### `volume_to_weight(ingredient, value, volume_unit, weight_unit)`
```python
volume_to_weight("table salt", 1, "tbsp", "g")   # → ~18.0 g
volume_to_weight("all-purpose flour", 1, "cup", "g")  # → ~125 g
```

### `weight_to_volume(ingredient, value, weight_unit, volume_unit)`
```python
weight_to_volume("table salt", 1, "g", "ml")     # → ~0.82 ml
weight_to_volume("granulated sugar", 200, "g", "cup")  # → ~1.0 cup
```

### `list_ingredients()`
Returns every known ingredient with its density and a note (e.g. *"1 cup ~ 125 g"*).

---

## Countable items: count ↔ weight

A separate table gives the weight of **one piece** of countable ingredients, so
counts can be turned into grams (and recipes with eggs/cloves can be scaled by
weight). See [`data/item_weights.json`](../data/item_weights.json).

### `item_weight(item)` / `list_item_weights()`
```python
item_weight("egg")      # → {"item": "egg", "grams_each": 50}
```

### `count_to_weight(item, count, weight_unit)` / `weight_to_count(...)`
```python
count_to_weight("egg", 2)          # → 100 g
count_to_weight("garlic", 3)       # → 15 g  ("garlic clove" ≈ 5 g)
weight_to_count("potato", 340)     # → ~2 potatoes
```
Names are matched tolerantly: *"fresh basil"* → `basil`, *"red bell pepper"* →
`bell pepper`. These weights also feed `recipe_to_percentages`,
`bakers_percentages` and weight-based scaling, so a recipe listing "2 eggs"
still has a total weight. Units like `pinch`/`dash` count as ~0 g.

---

> **Accuracy note:** densities are *bulk / scooped* values tuned to common
> cooking charts, not laboratory material density. Granular ingredients vary with
> packing — treat them as close approximations. Add your own with a
> [densities override](CONFIGURATION.md#custom-ingredient-densities).

---

## Scaling, percentages & ratios

### `scale_recipe(ingredients_list, factor | from_yield + to_yield)`
```python
scale_recipe(
    [{"name": "flour", "amount": 300, "unit": "g"},
     {"name": "sugar", "amount": 150, "unit": "g"}],
    from_yield=8, to_yield=12)
# → {"factor": 1.5,
#    "ingredients": [{"name":"flour","amount":450.0,"unit":"g"},
#                    {"name":"sugar","amount":225.0,"unit":"g"}]}
```
`scale_recipe(lines, factor=0.5)` halves a batch. Units are preserved; amounts
are simply multiplied, so this works for any unit.

### `recipe_to_percentages(ingredients_list)`
Each ingredient as a share of total weight. Volume units are converted to grams
via density, so names must be known ingredients.
```python
recipe_to_percentages([
    {"name": "flour", "amount": 100, "unit": "g"},
    {"name": "water", "amount": 100, "unit": "g"}])
# → total_grams 200; flour 50%, water 50%
```

### `bakers_percentages(ingredients_list, flour_keyword="flour")`
Flour is 100%; every other ingredient is a percentage of total flour weight.
```python
bakers_percentages([
    {"name": "bread flour", "amount": 1000, "unit": "g"},
    {"name": "water",       "amount": 700,  "unit": "g"},
    {"name": "salt",        "amount": 20,   "unit": "g"},
    {"name": "yeast",       "amount": 7,    "unit": "g"}])
# → flour_grams 1000; water 70%, salt 2%, yeast 0.7%
```
Any ingredient whose name contains the `flour_keyword` counts toward flour
(so blends of two flours sum correctly). Change the keyword for non-flour bases.

### `apply_bakers_percentages(formula, flour_grams)`
The inverse: turn a formula into real weights for a chosen flour weight.
```python
apply_bakers_percentages(
    {"flour": 100, "water": 65, "salt": 2}, flour_grams=500)
# → water 325 g, salt 10 g, total 835 g
```

### `solve_ratio(parts, total | known_name + known_amount, unit="g")`
```python
solve_ratio({"flour": 3, "water": 2, "salt": 1}, total=600)
# → flour 300, water 200, salt 100

solve_ratio({"flour": 3, "water": 2}, known_name="flour", known_amount=450)
# → water 300  (flour fixed at 450)
```

---

## Local cooking assistant (Ollama)

### `assistant_health()`
```python
assistant_health()
# → {"reachable": true, "host": "http://localhost:11434",
#    "model": "gemma3n:latest", "model_available": true,
#    "installed_models": ["gemma3n:latest"]}
```

### `assistant_models()`
Lists the models installed in your local Ollama instance.

### `cooking_assistant(question, context?, model?, temperature?)`
```python
cooking_assistant("Why weigh flour instead of using cups?")
# → {"model": "gemma3n:latest", "answer": "Cup measures vary with how the
#    flour is packed; weighing in grams gives consistent results."}
```
Pass `context` to give the model recipe text to reason over, or override
`model`/`temperature` for a single call.

### `get_config()` / `set_config(...)`
```python
set_config(model="llama3.1", temperature=0.3, persist=True)
# updates this session and writes config.json
```

See [CONFIGURATION.md](CONFIGURATION.md) for all settings.

---

## Recipe storage

Recipes are stored as JSON under the [data directory](CONFIGURATION.md#data-directory).

### `save_recipe(name, ingredients_list, steps?, servings?, ...)`
```python
save_recipe(
    "Sourdough Loaf",
    [{"name": "bread flour", "amount": 500, "unit": "g"},
     {"name": "water",       "amount": 350, "unit": "g"},
     {"name": "salt",        "amount": 10,  "unit": "g"}],
    steps=["Autolyse", "Mix", "Bulk ferment", "Shape", "Bake"],
    servings=1, yield_unit="loaf", tags=["bread"])
# → stored recipe incl. "id": "sourdough-loaf"
```

### `list_recipes()` / `search_recipes(query)` / `get_recipe(id)`
```python
search_recipes("bread")        # by name, tag, ingredient, note or source
get_recipe("sourdough-loaf")   # full recipe
```

### `set_recipe_ingredient_unit(recipe_id, ingredient, new_unit)`
Change how an ingredient is stored, converting the amount (incl. weight↔volume):
```python
set_recipe_ingredient_unit("pancakes", "all-purpose flour", "g")
# 1 cup flour  ->  ~125 g, saved back to the recipe
```

### `scale_stored_recipe(recipe_id, servings? | target_weight_g? | factor?, save_as?)`
```python
scale_stored_recipe("sourdough-loaf", target_weight_g=1720)   # ~2x a 860 g dough
scale_stored_recipe("pancakes", servings=12, save_as="Pancakes (party)")
```

---

## Cooking sessions (cook-along)

A live, scaled walk-through of a recipe with step tracking.

### `start_cooking(recipe_id, servings? | target_weight_g? | factor?)`
```python
start_cooking("sourdough-loaf", target_weight_g=1720)
# → session_id, scaled ingredients, "current_step", "next_steps", progress "0/7"
```

### `cooking_status(session_id)` / `complete_step(session_id, step_index?)`
```python
complete_step(sid)            # marks the current step done, returns the next one
complete_step(sid, 3)         # mark a specific step (0-based) done
uncomplete_step(sid, 3)       # re-open it
```

### `rescale_cooking(session_id, ...)` / `log_cooking(session_id, note)`
```python
rescale_cooking(sid, factor=2)                 # decided to make a double batch
log_cooking(sid, "dough slack — added 15 g flour")
```

### `finish_cooking(session_id)` / `list_cooking_sessions(include_finished?)`
```python
list_cooking_sessions()       # active cooks and their progress
finish_cooking(sid)
```
