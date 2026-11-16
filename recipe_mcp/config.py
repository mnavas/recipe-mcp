"""Runtime configuration for the recipe MCP server.

Resolution order (first found wins per field):
  1. environment variables (RECIPE_MCP_*)
  2. a config JSON file (RECIPE_MCP_CONFIG, else ./config.json)
  3. built-in defaults
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_SYSTEM_PROMPT = (
    "You are a concise, practical home-cooking and baking assistant. "
    "Give clear, step-by-step answers and prefer weights (grams) over volumes "
    "for baking. You are a language model, not a calculator: do NOT compute or "
    "guess unit, weight-to-volume, temperature or scaling conversions, and never "
    "invent a density or a number. For any such conversion, tell the user to use "
    "recipe-mcp's exact tools (for example weight_to_volume, convert_temperature "
    "or scale_recipe) instead of answering with a figure. "
    "Flag food-safety issues. Do not invent exact nutrition facts."
)


def default_data_dir() -> str:
    """Where recipes and cooking sessions are stored (XDG data dir)."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "recipe-mcp")


@dataclass
class Config:
    ollama_host: str = "http://localhost:11434"
    model: str = "gemma3n:latest"
    temperature: float = 0.4
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    densities_override: str = ""  # optional path to a user densities JSON
    item_weights_override: str = ""  # optional path to a user item-weights JSON
    data_dir: str = ""            # recipes + sessions; blank => default_data_dir()

    def resolved_data_dir(self) -> str:
        return self.data_dir or default_data_dir()


def _config_path() -> Path:
    return Path(os.environ.get("RECIPE_MCP_CONFIG", "config.json"))


def load_config() -> Config:
    cfg = Config()
    path = _config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for f in cfg.__dataclass_fields__:
                if f in data:
                    setattr(cfg, f, data[f])
        except (json.JSONDecodeError, OSError):
            pass

    env = os.environ
    if "RECIPE_MCP_OLLAMA_HOST" in env:
        cfg.ollama_host = env["RECIPE_MCP_OLLAMA_HOST"]
    if "RECIPE_MCP_MODEL" in env:
        cfg.model = env["RECIPE_MCP_MODEL"]
    if "RECIPE_MCP_TEMPERATURE" in env:
        try:
            cfg.temperature = float(env["RECIPE_MCP_TEMPERATURE"])
        except ValueError:
            pass
    if "RECIPE_MCP_SYSTEM_PROMPT" in env:
        cfg.system_prompt = env["RECIPE_MCP_SYSTEM_PROMPT"]
    if "RECIPE_MCP_DENSITIES" in env:
        cfg.densities_override = env["RECIPE_MCP_DENSITIES"]
    if "RECIPE_MCP_ITEM_WEIGHTS" in env:
        cfg.item_weights_override = env["RECIPE_MCP_ITEM_WEIGHTS"]
    if "RECIPE_MCP_DATA_DIR" in env:
        cfg.data_dir = env["RECIPE_MCP_DATA_DIR"]
    return cfg


def save_config(cfg: Config, path: str | Path | None = None) -> str:
    path = Path(path) if path else _config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    return str(path)
