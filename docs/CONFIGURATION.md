# recipe-mcp — configuration

All runtime settings live in [`recipe_mcp/config.py`](../recipe_mcp/config.py).
They resolve in this order, **first match wins per field**:

1. Environment variables (`RECIPE_MCP_*`)
2. A JSON config file
3. Built-in defaults

## Settings

| Field | Env var | Default | Meaning |
|-------|---------|---------|---------|
| `model` | `RECIPE_MCP_MODEL` | `llama3.2:latest` | Ollama model for the assistant |
| `ollama_host` | `RECIPE_MCP_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `temperature` | `RECIPE_MCP_TEMPERATURE` | `0.4` | Sampling temperature |
| `system_prompt` | `RECIPE_MCP_SYSTEM_PROMPT` | cooking-assistant persona | System message for the assistant |
| `densities_override` | `RECIPE_MCP_DENSITIES` | *(none)* | Path to a custom densities JSON |
| `item_weights_override` | `RECIPE_MCP_ITEM_WEIGHTS` | *(none)* | Path to a custom piece-weights JSON |
| `altitude_m` | `RECIPE_MCP_ALTITUDE_M` | `0` | Home altitude in metres — the default for the altitude tools |
| `data_dir` | `RECIPE_MCP_DATA_DIR` | `~/.local/share/recipe-mcp` | Where recipes & cooking sessions are stored |

## Data directory

Stored recipes and in-progress cooking sessions are plain JSON files:

```
<data_dir>/
  recipes/<recipe-id>.json     # one file per saved recipe
  sessions/<session-id>.json   # one file per cooking session
```

The default is `$XDG_DATA_HOME/recipe-mcp` (i.e. `~/.local/share/recipe-mcp`).
Point `data_dir` / `RECIPE_MCP_DATA_DIR` elsewhere to keep recipes in, say, a
synced folder. Because they're per-file JSON, they're easy to back up, diff, or
edit by hand.

## Config file

By default the server reads `config.json` from the working directory. Point it
elsewhere with `RECIPE_MCP_CONFIG=/path/to/config.json`.

Start from the template:

```bash
cp config.example.json config.json
```

```json
{
  "ollama_host": "http://localhost:11434",
  "model": "llama3.2:latest",
  "temperature": 0.4,
  "system_prompt": "You are a concise, practical home-cooking and baking assistant...",
  "densities_override": ""
}
```

`config.json` is git-ignored, so your local settings never get committed.
The `set_config(..., persist=True)` tool writes this file for you.

## Setting the model per client

When registering the server with an MCP client you can set the model inline, so
different clients can use different models:

```json
{
  "mcpServers": {
    "recipe": {
      "command": "/home/mario/Code/recipe-mcp/.venv/bin/python",
      "args": ["-m", "recipe_mcp"],
      "env": {
        "RECIPE_MCP_MODEL": "llama3.1",
        "RECIPE_MCP_TEMPERATURE": "0.3"
      }
    }
  }
}
```

## Custom ingredient densities

The built-in table ([`data/densities.json`](../data/densities.json)) covers 40+
common ingredients. To add or override entries, create your own JSON file and
point `densities_override` at it. Both shapes are accepted:

```json
{
  "ingredients": {
    "rye flour":    {"density": 0.56, "note": "spooned"},
    "semolina":     {"density": 0.74}
  }
}
```

or a flat map:

```json
{ "rye flour": 0.56, "semolina": 0.74 }
```

Overrides are merged on top of the built-ins at startup (and can replace an
existing entry). Densities are in **g/ml**.

> Reminder: use *bulk / scooped* densities (how the ingredient sits in a cup or
> spoon), not material density, if you want the conversions to match everyday
> kitchen measuring.

## Custom piece weights

Countable ingredients (eggs, cloves, whole vegetables) have a separate table,
[`data/item_weights.json`](../data/item_weights.json), giving the weight of one
piece in grams. Extend or override it the same way, via `item_weights_override`
/ `RECIPE_MCP_ITEM_WEIGHTS`:

```json
{ "items": { "quail egg": {"grams": 9}, "roma tomato": 60 } }
```

Names are matched tolerantly — "fresh basil" resolves to `basil`, "red bell
pepper" to `bell pepper` — so you usually don't need an entry per variant.
