import math

import pytest

from recipe_mcp.cooking import CookingStore
from recipe_mcp.storage import RecipeStore


@pytest.fixture
def stores(tmp_path):
    recipes = RecipeStore(tmp_path)
    recipes.save(
        "Bread",
        [{"name": "bread flour", "amount": 500, "unit": "g"},
         {"name": "water", "amount": 350, "unit": "g"},
         {"name": "salt", "amount": 10, "unit": "g"}],
        steps=["Mix", "Knead", "Proof", "Bake"],
        servings=1, yield_unit="loaf")
    return recipes, CookingStore(tmp_path, recipes)


def test_start_scales_by_servings(stores):
    _, cook = stores
    s = cook.start("bread", servings=2)
    assert math.isclose(s["scale"]["factor"], 2.0)
    flour = next(i for i in s["ingredients"] if i["name"] == "bread flour")
    assert math.isclose(flour["amount"], 1000.0)
    assert s["current_step"]["text"] == "Mix"
    assert "0/4" in s["progress"]


def test_start_scales_by_target_weight(stores):
    _, cook = stores
    s = cook.start("bread", target_weight_g=1720)  # base total 860 g -> x2
    assert math.isclose(s["scale"]["factor"], 2.0, rel_tol=1e-6)


def test_step_progression(stores):
    _, cook = stores
    s = cook.start("bread")
    sid = s["session_id"]
    s = cook.complete_step(sid)                 # completes "Mix"
    assert s["current_step"]["text"] == "Knead"
    assert "1/4" in s["progress"]
    s = cook.complete_step(sid, step_index=3)   # complete "Bake" out of order
    assert any(d["text"] == "Bake" for d in s["done_steps"])
    assert "2/4" in s["progress"]


def test_rescale_keeps_progress(stores):
    _, cook = stores
    s = cook.start("bread")
    sid = s["session_id"]
    cook.complete_step(sid)
    s = cook.rescale(sid, factor=3)
    flour = next(i for i in s["ingredients"] if i["name"] == "bread flour")
    assert math.isclose(flour["amount"], 1500.0)
    assert "1/4" in s["progress"]  # progress preserved


def test_log_and_finish_and_list(stores):
    _, cook = stores
    s = cook.start("bread")
    sid = s["session_id"]
    s = cook.log(sid, "dough sticky, added flour")
    assert s["log"][0]["note"].startswith("dough sticky")
    assert cook.list()  # active session listed
    cook.finish(sid)
    assert cook.list() == []                    # finished hidden by default
    assert cook.list(include_finished=True)


def test_all_steps_done_status(stores):
    _, cook = stores
    s = cook.start("bread")
    sid = s["session_id"]
    for _ in range(4):
        s = cook.complete_step(sid)
    assert s["status"] == "done_steps"
    assert s["current_step"] is None
    with pytest.raises(ValueError):
        cook.complete_step(sid)
