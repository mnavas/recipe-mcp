# recipe-mcp

A local [MCP](https://modelcontextprotocol.io) server for the kitchen. It gives
any MCP client (Claude Desktop, Claude Code, etc.) tools to:

- **Convert units** — weight (mg/g/kg/oz/lb/stone) and volume (ml/l/cup/tbsp/tsp/fl oz, US + metric + imperial).
- **Convert weight ↔ volume per ingredient** — using a bulk-density table, so "how many grams is 1 tbsp of table salt?" or "how much volume is 1 g of salt?" are answerable when your scale isn't precise to the gram.
- **Scale recipes** — by a factor or by changing the yield (e.g. 8 → 12 servings).
- **Percentages & ratios** — ingredient-as-%-of-total, **baker's percentages** (flour = 100%), and solving ratios like 3:2:1.
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

## Run

```bash
python -m recipe_mcp      # stdio transport
```

### Register with an MCP client

Claude Desktop / Claude Code `mcpServers` entry:

```json
{
  "mcpServers": {
    "recipe": {
      "command": "/home/mario/Code/recipe-mcp/.venv/bin/python",
      "args": ["-m", "recipe_mcp"],
      "env": { "RECIPE_MCP_MODEL": "gemma3n:latest" }
    }
  }
}
```

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
| `cooking_assistant` | Ask the local Ollama assistant |
| `assistant_models` / `assistant_health` | List models / check Ollama |
| `get_config` / `set_config` | View or change model, host, temperature, prompt |

An ingredient line used by the scaling tools is `{"name", "amount", "unit"}`.

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

`set_config(..., persist=True)` writes `config.json` for you.

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
  config.py       settings (env / config.json / defaults)
data/densities.json
docs/             landing page + EXAMPLES.md + CONFIGURATION.md
tests/
```

## License

MIT — see [LICENSE](LICENSE).
