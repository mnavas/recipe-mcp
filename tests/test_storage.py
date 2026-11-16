import math

import pytest

from recipe_mcp.storage import RecipeStore, slugify


@pytest.fixture
def store(tmp_path):
    return RecipeStore(tmp_path)


def _pancakes(store):
    return store.save(
        "Pancakes",
        [{"name": "all-purpose flour", "amount": 1, "unit": "cup"},
         {"name": "milk", "amount": 1, "unit": "cup"},
         {"name": "granulated sugar", "amount": 2, "unit": "tbsp"}],
        steps=["Mix dry", "Add milk", "Cook on griddle"],
        servings=4, tags=["breakfast"])


def test_save_and_get(store):
    r = _pancakes(store)
    assert r["id"] == "pancakes"
    got = store.get("pancakes")
    assert got["name"] == "Pancakes"
    assert len(got["ingredients"]) == 3
    assert got["servings"] == 4


def test_slugify():
    assert slugify("Mom's Best  Bread!!") == "mom-s-best-bread"


def test_list_and_search(store):
    _pancakes(store)
    assert any(s["id"] == "pancakes" for s in store.list())
    assert store.search("breakfast")
    assert store.search("flour")
    assert store.search("nonexistent") == []


def test_update(store):
    _pancakes(store)
    r = store.update("pancakes", {"servings": 8, "notes": "double"})
    assert r["servings"] == 8 and r["notes"] == "double"


def test_set_ingredient_unit_cross(store):
    _pancakes(store)
    # 1 cup flour -> grams (density 0.53): ~125 g
    r = store.set_ingredient_unit("pancakes", "all-purpose flour", "g")
    flour = next(i for i in r["ingredients"] if i["name"] == "all-purpose flour")
    assert flour["unit"] == "g"
    assert math.isclose(flour["amount"], 236.5882365 * 0.53, rel_tol=1e-6)


def test_delete(store):
    _pancakes(store)
    assert store.delete("pancakes") is True
    assert store.delete("pancakes") is False
    with pytest.raises(ValueError):
        store.get("pancakes")


def test_bad_ingredients(store):
    with pytest.raises(ValueError):
        store.save("x", [])
    with pytest.raises(ValueError):
        store.save("x", [{"name": "flour"}])  # missing amount
