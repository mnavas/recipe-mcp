import math

from recipe_mcp import scaling


def test_scale_by_factor():
    r = scaling.scale_recipe([{"name": "flour", "amount": 100, "unit": "g"}], factor=2)
    assert r["ingredients"][0]["amount"] == 200
    assert r["factor"] == 2


def test_scale_by_yield():
    r = scaling.scale_recipe(
        [{"name": "flour", "amount": 300, "unit": "g"}], from_yield=8, to_yield=12)
    assert math.isclose(r["factor"], 1.5)
    assert math.isclose(r["ingredients"][0]["amount"], 450)


def test_percentages():
    r = scaling.to_percentages([
        {"name": "flour", "amount": 100, "unit": "g"},
        {"name": "water", "amount": 100, "unit": "g"},
    ])
    assert math.isclose(r["total_grams"], 200)
    assert math.isclose(r["ingredients"][0]["percent"], 50.0)


def test_bakers_percentages():
    r = scaling.bakers_percentages([
        {"name": "bread flour", "amount": 1000, "unit": "g"},
        {"name": "water", "amount": 650, "unit": "g"},
        {"name": "salt", "amount": 20, "unit": "g"},
    ])
    assert math.isclose(r["flour_grams"], 1000)
    pcts = {row["name"]: row["bakers_percent"] for row in r["ingredients"]}
    assert math.isclose(pcts["water"], 65.0)
    assert math.isclose(pcts["salt"], 2.0)


def test_apply_bakers_percentages():
    r = scaling.apply_bakers_percentages(
        {"flour": 100, "water": 65, "salt": 2}, flour_grams=500)
    g = {row["name"]: row["grams"] for row in r["ingredients"]}
    assert math.isclose(g["water"], 325.0)
    assert math.isclose(g["salt"], 10.0)


def test_solve_ratio_by_total():
    r = scaling.solve_ratio({"flour": 3, "water": 2, "salt": 1}, total=600)
    amounts = {row["name"]: row["amount"] for row in r["ingredients"]}
    assert math.isclose(amounts["flour"], 300)
    assert math.isclose(amounts["salt"], 100)


def test_solve_ratio_by_known():
    r = scaling.solve_ratio({"flour": 3, "water": 2}, known_name="flour", known_amount=450)
    amounts = {row["name"]: row["amount"] for row in r["ingredients"]}
    assert math.isclose(amounts["water"], 300)
