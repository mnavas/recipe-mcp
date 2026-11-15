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
    "Give clear, step-by-step answers. Prefer weights (grams) over volumes for "
    "baking. When asked to convert or scale, show the arithmetic briefly. "
    "Flag food-safety issues. Do not invent exact nutrition facts."
)


@dataclass
class Config:
    ollama_host: str = "http://localhost:11434"
    model: str = "gemma3n:latest"
    temperature: float = 0.4
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    densities_override: str = ""  # optional path to a user densities JSON


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
    return cfg


def save_config(cfg: Config, path: str | Path | None = None) -> str:
    path = Path(path) if path else _config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    return str(path)
