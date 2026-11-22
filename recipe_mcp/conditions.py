"""Assorted kitchen-condition helpers: humidity, pressure cooker, gelatin,
oven calibration."""

from __future__ import annotations

from . import units


# --- humidity --------------------------------------------------------------- #
def humidity_tip(humidity_percent: float | None = None) -> dict:
    """Dough/batter guidance for the day's relative humidity."""
    if humidity_percent is None:
        return {"tips": [
            "Flour's moisture tracks the air: add liquid by feel, not just by the recipe.",
            "Humid days → hold back a little liquid; dry days → add a little.",
        ]}
    h = float(humidity_percent)
    if h < 40:
        band, tips = "dry", [
            "Flour is dry and thirsty — add ~1 tbsp extra liquid per cup of flour, by feel.",
            "Doughs stiffen and breads can dry out; cover rising dough well.",
        ]
    elif h <= 60:
        band, tips = "normal", ["Comfortable range — follow the recipe and adjust by feel."]
    else:
        band, tips = "humid", [
            "Flour holds extra water — hold back ~1-2 tbsp liquid per cup of flour (or add flour).",
            "Sugar and salt can clump; meringues, caramel and candy weep — pick a drier day if you can.",
        ]
    return {"humidity_percent": h, "band": band, "tips": tips}


# --- pressure cooker -------------------------------------------------------- #
def pressure_cooker_time(conventional_minutes: float, altitude_m: float = 0) -> dict:
    """Rough pressure-cooker time from a conventional simmer/boil time.

    Pressure cooking runs ~3x faster; at altitude, stovetop cookers need a bit
    more time. These are estimates — follow a tested recipe when you have one.
    """
    base = conventional_minutes / 3.0
    low, high = conventional_minutes / 4.0, conventional_minutes / 3.0
    alt_pct = 0.0
    if altitude_m > 600:
        alt_pct = 5.0 * ((altitude_m - 600) / 300.0)  # ~+5% per 300 m above 600 m
        base *= (1 + alt_pct / 100.0)
    note = "~1/4 to 1/3 of the conventional time."
    if alt_pct:
        note += f" +~{round(alt_pct)}% added for altitude (stovetop cookers lose pressure up high)."
    return {"conventional_minutes": conventional_minutes,
            "estimate_minutes": round(base, 1),
            "range_minutes": [round(low, 1), round(high, 1)],
            "altitude_m": round(altitude_m), "note": note}


# --- gelatin ---------------------------------------------------------------- #
GELATIN_SHEET_G = 2.0      # one sheet ≈ 2 g (bloom-standardised)
GELATIN_TSP_G = 3.1       # powdered gelatin: 1 tsp ≈ 3.1 g (1 envelope ≈ 7 g)


def convert_gelatin(amount: float, from_type: str, to_type: str) -> dict:
    """Convert gelatin between sheets and powder (by gelling weight).

    `from_type`/`to_type`: "sheet" (amount = number of sheets) or
    "powder" (amount = grams).
    """
    f, t = from_type.strip().lower(), to_type.strip().lower()
    if f in ("sheet", "leaf", "sheets"):
        grams = amount * GELATIN_SHEET_G
    elif f in ("powder", "powdered", "granulated"):
        grams = amount
    else:
        raise ValueError("from_type must be 'sheet' or 'powder'")
    out = {"grams": round(grams, 2)}
    if t in ("sheet", "leaf", "sheets"):
        out["sheets"] = round(grams / GELATIN_SHEET_G, 2)
    elif t in ("powder", "powdered", "granulated"):
        out["powder_grams"] = round(grams, 2)
        out["powder_tsp"] = round(grams / GELATIN_TSP_G, 2)
    else:
        raise ValueError("to_type must be 'sheet' or 'powder'")
    return out


# --- oven calibration ------------------------------------------------------- #
def oven_calibration(set_temp: float, actual_temp: float, target_temp: float,
                     unit: str = "C") -> dict:
    """Given how far your oven runs off (measured), what dial setting hits a target.

    offset = actual − set. To get `target` inside, set it to target − offset.
    """
    offset = actual_temp - set_temp
    set_to = target_temp - offset
    direction = "hot" if offset > 0 else ("cold" if offset < 0 else "accurate")
    return {"measured_offset": round(offset, 1), "runs": direction,
            "target": target_temp, "set_dial_to": round(set_to, 1),
            "unit": unit.upper().lstrip("°"),
            "note": f"Your oven runs {abs(round(offset,1))} deg {direction}; "
                    f"set the dial to {round(set_to,1)} to get {target_temp} inside."}
