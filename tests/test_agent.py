import sys
import types

import pytest

from recipe_mcp import agent
from recipe_mcp.config import Config


def test_dispatch_runs_real_tools(tmp_path):
    d = agent._mk_dispatch(Config(data_dir=str(tmp_path)))
    assert round(d["ingredient_volume_to_weight"]("table salt", 1, "ml", "g")["result"], 2) == 1.22
    assert d["convert_temperature"](180, "C", "F")["result"] == 356.0
    assert d["count_to_weight"]("egg", 2)["result"] == 100.0


def test_call_fields_parses_dict_and_string():
    tc = {"function": {"name": "convert_weight", "arguments": {"value": 1, "from_unit": "kg", "to_unit": "g"}}}
    assert agent._call_fields(tc) == ("convert_weight", {"value": 1, "from_unit": "kg", "to_unit": "g"})
    tc2 = {"function": {"name": "x", "arguments": '{"a": 1}'}}
    assert agent._call_fields(tc2) == ("x", {"a": 1})


def _fake_ollama(script):
    """Build a fake `ollama` module whose Client.chat yields canned responses."""
    calls = {"i": 0}

    class Client:
        def __init__(self, host=None):
            pass

        def chat(self, model, messages, tools=None, options=None):
            resp = script[min(calls["i"], len(script) - 1)]
            calls["i"] += 1
            return resp

    mod = types.ModuleType("ollama")
    mod.Client = Client
    return mod


def test_run_executes_tool_then_answers(tmp_path, monkeypatch):
    # 1st turn: model asks to call the salt conversion; 2nd turn: it answers.
    script = [
        {"message": {"content": "", "tool_calls": [
            {"function": {"name": "ingredient_volume_to_weight",
                          "arguments": {"ingredient": "table salt", "value": 1, "volume_unit": "ml", "weight_unit": "g"}}}]}},
        {"message": {"content": "1 ml of table salt weighs about 1.22 g.", "tool_calls": []}},
    ]
    monkeypatch.setitem(sys.modules, "ollama", _fake_ollama(script))
    out = agent.run(Config(data_dir=str(tmp_path)), "how much does 1 ml of salt weigh?")
    assert "1.22" in out["answer"]
    assert out["tool_calls"][0]["tool"] == "ingredient_volume_to_weight"
    assert round(out["tool_calls"][0]["result"]["result"], 2) == 1.22


def test_run_plain_answer_without_tools(tmp_path, monkeypatch):
    script = [{"message": {"content": "Use a cool, dry place.", "tool_calls": []}}]
    monkeypatch.setitem(sys.modules, "ollama", _fake_ollama(script))
    out = agent.run(Config(data_dir=str(tmp_path)), "how do I store salt?")
    assert out["answer"].startswith("Use a cool")
    assert out["tool_calls"] == []
