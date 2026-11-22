# recipe-mcp

A local [MCP](https://modelcontextprotocol.io) server for the kitchen. It gives
any MCP client (Claude Desktop, Claude Code, etc.) tools to:

- **Convert units** — weight (mg/g/kg/oz/lb/stone) and volume (ml/l/cup/tbsp/tsp/fl oz, US + metric + imperial).
- **Convert weight ↔ volume per ingredient** — using a bulk-density table, so "how many grams is 1 tbsp of table salt?" or "how much volume is 1 g of salt?" are answerable when your scale isn't precise to the gram.
- **Convert counts ↔ weight** — a piece-weight table (1 egg ≈ 50 g, 1 garlic clove ≈ 5 g) so "2 eggs" has a weight, and recipes with countable items can still be scaled by total weight.
- **Temperature & oven** — °C/°F/°K conversion, UK gas marks, fan-oven adjustment, and a one-stop oven breakdown (e.g. 180 °C → 356 °F, gas 4, fan 160 °C, "moderate").
- **Altitude** — water's boiling point at your elevation (why things boil cooler and take longer), high-altitude baking adjustments (leavening, sugar, liquid, oven temp), and yeast-type conversion (fresh ↔ active dry ↔ instant).
- **Conditions & substitutions** — salt-type swaps (table ↔ kosher ↔ flaky, equal saltiness), gelatin sheets ↔ powder, pan-size scaling by area, scaling caveats (what doesn't scale linearly), humidity tips, pressure-cooker timing, and oven-calibration offset.
- **Scale recipes** — by a factor or by changing the yield (e.g. 8 → 12 servings).
- **Percentages & ratios** — ingredient-as-%-of-total, **baker's percentages** (flour = 100%), and solving ratios like 3:2:1.
- **Store & retrieve recipes** — save recipes, search them, adjust servings/target weight, and even change an ingredient's stored unit.
- **Cook along** — start a cooking session from a recipe, scaled to your batch; the assistant tracks what's done and what's next, step by step.
- **Ask a local cooking assistant** — backed by [Ollama](https://ollama.com) running on your machine (default model `llama3.2:latest`).

Everything runs locally. The assistant never leaves your computer.

## Install

```bash
cd recipe-mcp
python3 -m venv .venv && . .venv/bin/activate
pip install -e .          # or: pip install -r requirements.txt
```

Make sure Ollama is running and has a model:

```bash
ollama serve &            # usually already running as a service
ollama pull llama3.2       # or any model you like
```

## How to use it

**recipe-mcp is a backend for an AI assistant, not an app you run by hand.**
`python -m recipe_mcp` starts the server and then just waits silently — that's
correct: it speaks the MCP protocol over stdin/stdout and does nothing until an
**MCP client** (Claude Desktop, Claude Code, …) connects and calls its tools.
You then talk to that client in plain language and it calls the tools for you.

There are three ways to use it, from quickest to most integrated.

### 1. Straight from the terminal (no client needed)

A small CLI exposes the same conversions directly — handy for a quick check:

```bash
recipe-mcp-cli convert 2 cup ml            # 2.0 cup = 473.2 ml
recipe-mcp-cli convert 1 lb g              # 1.0 lb = 453.6 g
recipe-mcp-cli vtow "table salt" 1 tbsp g  # 1 tbsp salt = 18.04 g
recipe-mcp-cli wtov "all-purpose flour" 125 g cup
recipe-mcp-cli ingredients                 # list the density table
recipe-mcp-cli oven 180 C                  # 180C = 356F · gas 4 · fan 160C
recipe-mcp-cli boil 2850 m                 # water boils at 90C at 2850 m
recipe-mcp-cli ask "why weigh flour instead of cups?"   # needs Ollama
```

(Equivalent to `python -m recipe_mcp.cli …` if the script isn't on your PATH.)

### 2. Claude Code

Register the server once, then just ask in chat:

```bash
claude mcp add recipe -- /ABSOLUTE/PATH/recipe-mcp/.venv/bin/python -m recipe_mcp
```

Then: *"Using the recipe tools, convert 2 cups of flour to grams"* or
*"Give me the baker's percentages for 1000 g flour, 700 g water, 20 g salt."*
Check it's connected with `claude mcp list`.

### 3. Claude Desktop

Edit the config file (**Settings → Developer → Edit Config**, or the path below)
and add the server. Use the **absolute path** to the venv's Python:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "recipe": {
      "command": "/ABSOLUTE/PATH/recipe-mcp/.venv/bin/python",
      "args": ["-m", "recipe_mcp"],
      "env": { "RECIPE_MCP_MODEL": "llama3.2:latest" }
    }
  }
}
```

Restart Claude Desktop; the recipe tools appear in the 🔌 tools menu.

### Inspect the tools in a browser (optional)

To click through every tool manually, run the official MCP Inspector against the
server (needs Node/npx; no `uv` required):

```bash
npx @modelcontextprotocol/inspector .venv/bin/python -m recipe_mcp
```

> The bundled `mcp install` / `mcp dev` helpers are **not** used here because they
> require `uv`; the commands above work with a plain venv.

### Example prompts (once connected)

- "How many grams is 1 tablespoon of table salt?"
- "Scale this recipe from 8 to 12 servings: 300 g flour, 150 g sugar, 2 eggs."
- "Turn this into baker's percentages." / "Apply these percentages to 500 g flour."
- "What's a 3:2:1 shortbread ratio for 600 g total?"

## Tools

| Tool | What it does |
|------|--------------|
| `convert_weight` / `convert_volume` | Unit conversion within a dimension |
| `list_units` | All supported unit names |
| `list_ingredients` / `ingredient_density` | Browse the density table (g/ml) |
| `weight_to_volume` / `volume_to_weight` | Per-ingredient weight ↔ volume |
| `list_item_weights` / `item_weight` | Browse / get the weight of one piece (1 egg ≈ 50 g) |
| `count_to_weight` / `weight_to_count` | Convert counts ↔ grams (2 eggs → 100 g) |
| `convert_temperature` | °C ↔ °F ↔ °K |
| `oven_temperature` | Full oven breakdown: C, F, gas mark, fan, description |
| `gas_mark_to_temperature` | UK gas mark → °C/°F |
| `fan_oven` | Conventional ↔ fan-oven temperature |
| `water_boiling_point` | Boiling point at an altitude (+ cooking note) |
| `altitude_baking_adjustments` | High-altitude recipe fixes (leavening, sugar, liquid, oven) |
| `convert_yeast` | Fresh ↔ active dry ↔ instant yeast |
| `convert_salt` | Table ↔ kosher ↔ flaky, equal saltiness |
| `convert_gelatin` | Sheets ↔ powder |
| `scale_for_pan` | Move a recipe between pan sizes (by area) |
| `scaling_caveats` | What doesn't scale linearly (leavening, salt, time) |
| `humidity_tip` | Dough advice for the day's humidity |
| `pressure_cooker_time` | Conventional → pressure-cooker time (altitude-aware) |
| `oven_calibration` | Dial setting for your oven's real temperature |
| `scale_recipe` | Rescale by `factor` or `from_yield`/`to_yield` |
| `recipe_to_percentages` | Each ingredient as % of total weight |
| `bakers_percentages` | Flour = 100%, others relative to flour |
| `apply_bakers_percentages` | Turn a formula into weights for a flour weight |
| `solve_ratio` | Scale a ratio (e.g. 3:2:1) to real amounts |
| `save_recipe` / `get_recipe` | Store / retrieve a recipe |
| `list_recipes` / `search_recipes` | Browse / find stored recipes |
| `update_recipe` / `delete_recipe` | Edit / remove a recipe |
| `set_recipe_ingredient_unit` | Change an ingredient's stored unit (converts the amount) |
| `scale_stored_recipe` | Scale a stored recipe by servings/weight/factor (optionally save) |
| `start_cooking` | Begin a cook-along, scaled to your batch |
| `cooking_status` | Scaled ingredients, steps done, and what's next |
| `complete_step` / `uncomplete_step` | Advance / re-open step progress |
| `rescale_cooking` | Re-scale an in-progress cook, keeping progress |
| `log_cooking` | Add a timestamped note to a cook |
| `finish_cooking` / `list_cooking_sessions` | End / list sessions |
| `cooking_assistant` | Ask the local Ollama assistant |
| `assistant_models` / `assistant_health` | List models / check Ollama |
| `get_config` / `set_config` | View or change model, host, temperature, prompt |

An ingredient line used by the scaling/recipe tools is `{"name", "amount", "unit"}`.

### Recipes & cook-along

Save a recipe once, then scale it or cook from it:

```bash
# import the bundled starter recipes, then browse them from the terminal
recipe-mcp-cli import examples/*.json
recipe-mcp-cli recipes
recipe-mcp-cli show pizza-dough
```

The `examples/` folder ships sixteen researched staples: no-knead bread,
sourdough, pizza dough, white rice, fresh pasta, pancakes, tomato sauce
(marinara), vinaigrette, béchamel, chocolate chip cookies, scrambled eggs,
boiled eggs, mashed potatoes, roast chicken, basic muffins, and an all-purpose
stir-fry sauce — with sourced ratios and weights in grams.

Through an MCP client you'd say things like *"save this recipe"*, *"scale the
sourdough loaf to 1.5 kg of dough"*, *"start cooking it"*, *"what's the next
step?"*, *"mark that done"*, or *"store the flour in grams instead of cups"* —
each maps to one of the tools above. Recipes and in-progress cooks are stored as
JSON under the [data directory](docs/CONFIGURATION.md) so they persist across
restarts.

### The local assistant can use the tools

`recipe-mcp-cli ask "..."` runs an **agentic loop**: the local model is given the
deterministic tools (conversions, densities, piece weights, recipe lookups) and
*calls them*, so answers are grounded in real numbers rather than guessed.

This needs a model that supports tool-calling. The default, **`llama3.2`**, does
(as do `llama3.1`, `qwen2.5`, `mistral`):

```bash
ollama pull llama3.2
recipe-mcp-cli ask "how many ml is 1 g of table salt?"
# → calls ingredient_volume_to_weight and answers 0.82 ml
```

Some models **don't** support tools — notably **`gemma3n`**. With one of those,
`ask` prints a note and falls back to a plain chat answer (don't trust its
numbers; use `wtov`/`convert`/`oven` or the math tools).

Use `ask --plain` to force a plain chat with no tools. (Inside a real MCP client
like Claude Desktop, the client's own model drives all 41 tools — this agentic
`ask` is the equivalent for the local CLI.)

## Configuration

Settings resolve in this order (first wins): **env vars → `config.json` → defaults**.
Copy `config.example.json` to `config.json` to persist, or use env vars:

| Field | Env var | Default |
|-------|---------|---------|
| `model` | `RECIPE_MCP_MODEL` | `llama3.2:latest` |
| `ollama_host` | `RECIPE_MCP_OLLAMA_HOST` | `http://localhost:11434` |
| `temperature` | `RECIPE_MCP_TEMPERATURE` | `0.4` |
| `system_prompt` | `RECIPE_MCP_SYSTEM_PROMPT` | cooking-assistant persona |
| `densities_override` | `RECIPE_MCP_DENSITIES` | *(none)* |
| `item_weights_override` | `RECIPE_MCP_ITEM_WEIGHTS` | *(none)* |
| `altitude_m` | `RECIPE_MCP_ALTITUDE_M` | `0` (home altitude in metres) |
| `data_dir` | `RECIPE_MCP_DATA_DIR` | `~/.local/share/recipe-mcp` |

`set_config(..., persist=True)` writes `config.json` for you. Recipes live in
`<data_dir>/recipes/` and cooking sessions in `<data_dir>/sessions/`.

## Ingredient densities

Densities in `data/densities.json` are **bulk (scooped) densities in g/ml**, tuned
to common cooking charts — not laboratory material density. Granular ingredients
vary with packing, so treat them as close approximations. Extend or override them
with your own JSON file via `densities_override` (accepts `{"ingredients": {...}}`
or a flat `{name: density}` map).

## Documentation

- [docs/EXAMPLES.md](docs/EXAMPLES.md) — every tool with worked example calls and outputs.
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) — all settings, config file, custom densities.
- [docs/index.html](docs/index.html) — project landing page (also serves via GitHub Pages).

## Tests

```bash
pip install pytest
python -m pytest -q
```

## Layout

```
recipe_mcp/
  server.py       MCP server — wires tools to the modules
  units.py        weight & volume conversion
  ingredients.py  density table + weight/volume conversion
  items.py        piece-weight table + count/weight conversion
  temperature.py  C/F/K, gas marks, fan oven, oven breakdown
  altitude.py     boiling point + high-altitude baking adjustments
  yeast.py        fresh / active dry / instant yeast conversion
  salt.py         salt-type swaps by volume (equal saltiness)
  pans.py         pan-size scaling by surface area
  conditions.py   humidity, pressure cooker, gelatin, oven calibration
  scaling.py      scaling, percentages, baker's %, ratios
  assistant.py    Ollama cooking assistant
  storage.py      recipe store (save/get/search/edit/convert units)
  cooking.py      cook-along sessions (scale + step tracking)
  config.py       settings (env / config.json / defaults)
  cli.py          terminal commands
data/densities.json      ingredient bulk densities (g/ml)
data/item_weights.json   piece weights for countable items (g each)
examples/         sixteen staple recipes to import
docs/             landing page + EXAMPLES.md + CONFIGURATION.md
tests/
```

## License

MIT — see [LICENSE](LICENSE).
