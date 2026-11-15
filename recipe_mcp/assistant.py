"""Ollama-backed local cooking assistant.

Thin wrapper over the `ollama` Python client, driven by Config. Kept free of
MCP so it can be reused or tested on its own.
"""

from __future__ import annotations

from .config import Config


def _client(cfg: Config):
    import ollama
    return ollama.Client(host=cfg.ollama_host)


def list_models(cfg: Config) -> list[str]:
    """Names of models installed in the local Ollama instance."""
    resp = _client(cfg).list()
    names = []
    for m in resp.get("models", []):
        name = m.get("model") or m.get("name")
        if name:
            names.append(name)
    return names


def ask(cfg: Config, question: str, *, context: str | None = None,
        model: str | None = None, temperature: float | None = None) -> str:
    """Ask the local cooking assistant a question and return its reply."""
    messages = [{"role": "system", "content": cfg.system_prompt}]
    if context:
        messages.append({"role": "system", "content": f"Relevant context:\n{context}"})
    messages.append({"role": "user", "content": question})

    resp = _client(cfg).chat(
        model=model or cfg.model,
        messages=messages,
        options={"temperature": cfg.temperature if temperature is None else temperature},
    )
    return resp["message"]["content"]


def health(cfg: Config) -> dict:
    """Check whether Ollama is reachable and the configured model is present."""
    try:
        models = list_models(cfg)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as data
        return {"reachable": False, "host": cfg.ollama_host, "error": str(exc)}
    return {
        "reachable": True,
        "host": cfg.ollama_host,
        "model": cfg.model,
        "model_available": cfg.model in models,
        "installed_models": models,
    }
