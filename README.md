# recipe-mcp

A local [MCP](https://modelcontextprotocol.io) server for the kitchen. It gives
any MCP client (Claude Desktop, Claude Code, etc.) tools to:

- **Convert units** — weight (mg/g/kg/oz/lb/stone) and volume (ml/l/cup/tbsp/tsp/fl oz, US + metric + imperial).
- **Convert weight ↔ volume per ingredient** — using a bulk-density table, so "how many grams is 1 tbsp of table salt?" or "how much volume is 1 g of salt?" are answerable when your scale isn't precise to the gram.
- **Scale recipes** — by a factor or by changing the yield (e.g. 8 → 12 servings).
- **Percentages & ratios** — ingredient-as-%-of-total, **baker's percentages** (flour = 100%), and solving ratios like 3:2:1.
- **Store & retrieve recipes** — save recipes, search them, adjust servings/target weight, and even change an ingredient's stored unit.
- **Cook along** — start a cooking session from a recipe, scaled to your batch; the assistant tracks what's done and what's next, step by step.
- **Ask a local cooking assistant** — backed by [Ollama](https://ollama.com) running on your machine (default model `gemma3n:latest`).

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
ollama pull gemma3n       # or any model you like
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
      "env": { "RECIPE_MCP_MODEL": "gemma3n:latest" }
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
# import the bundled example, then browse it from the terminal
recipe-mcp-cli import examples/sourdough-loaf.json
recipe-mcp-cli recipes
recipe-mcp-cli show sourdough-loaf
```

Through an MCP client you'd say things like *"save this recipe"*, *"scale the
sourdough loaf to 1.5 kg of dough"*, *"start cooking it"*, *"what's the next
step?"*, *"mark that done"*, or *"store the flour in grams instead of cups"* —
each maps to one of the tools above. Recipes and in-progress cooks are stored as
JSON under the [data directory](docs/CONFIGURATION.md) so they persist across
restarts.

## Configuration

Settings resolve in this order (first wins): **env vars → `config.json` → defaults**.
Copy `config.example.json` to `config.json` to persist, or use env vars:

| Field | Env var | Default |
|-------|---------|---------|
| `model` | `RECIPE_MCP_MODEL` | `gemma3n:latest` |
| `ollama_host` | `RECIPE_MCP_OLLAMA_HOST` | `http://localhost:11434` |
| `temperature` | `RECIPE_MCP_TEMPERATURE` | `0.4` |
| `system_prompt` | `RECIPE_MCP_SYSTEM_PROMPT` | cooking-assistant persona |
| `densities_override` | `RECIPE_MCP_DENSITIES` | *(none)* |
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
  scaling.py      scaling, percentages, baker's %, ratios
  assistant.py    Ollama cooking assistant
  storage.py      recipe store (save/get/search/edit/convert units)
  cooking.py      cook-along sessions (scale + step tracking)
  config.py       settings (env / config.json / defaults)
  cli.py          terminal commands
data/densities.json
examples/         a sample recipe to import
docs/             landing page + EXAMPLES.md + CONFIGURATION.md
tests/
```

## License

MIT — see [LICENSE](LICENSE).
