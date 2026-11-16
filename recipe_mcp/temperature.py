"""Temperature and oven conversions: C / F / K, UK gas marks, fan ovens.

Gas-mark and description tables use the common UK oven chart. Fan (convection)
ovens are taken to run ~20 C hotter than conventional, so the usual advice is to
set a fan oven 20 C lower than a conventional recipe temperature.
"""

from __future__ import annotations

# Gas mark -> (celsius, fahrenheit), standard UK oven chart.
GAS_MARKS: dict[float, tuple[int, int]] = {
    0.25: (110, 225),
    0.5: (130, 250),
    1: (140, 275),
    2: (150, 300),
    3: (170, 325),
    4: (180, 350),
    5: (190, 375),
    6: (200, 400),
    7: (220, 425),
    8: (230, 450),
    9: (240, 475),
}

FAN_OFFSET_C = 20  # a fan oven runs ~20 C hotter than conventional


def _norm(unit: str) -> str:
    u = unit.strip().lower().lstrip("°")
    return {"celsius": "c", "centigrade": "c", "fahrenheit": "f", "kelvin": "k"}.get(u, u)


def to_celsius(value: float, unit: str) -> float:
    u = _norm(unit)
    if u == "c":
        return value
    if u == "f":
        return (value - 32) * 5 / 9
    if u == "k":
        return value - 273.15
    raise ValueError(f"Unknown temperature unit {unit!r} (use C, F or K)")


def from_celsius(celsius: float, unit: str) -> float:
    u = _norm(unit)
    if u == "c":
        return celsius
    if u == "f":
        return celsius * 9 / 5 + 32
    if u == "k":
        return celsius + 273.15
    raise ValueError(f"Unknown temperature unit {unit!r} (use C, F or K)")


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    return from_celsius(to_celsius(value, from_unit), to_unit)


def parse_gas_mark(mark) -> float:
    """Accept 4, '4', '1/4', '0.25'."""
    if isinstance(mark, (int, float)):
        return float(mark)
    s = str(mark).strip().lower().replace("gas", "").replace("mark", "").strip()
    if "/" in s:
        num, den = s.split("/")
        return float(num) / float(den)
    return float(s)


def gas_mark_to_celsius(mark) -> int:
    m = parse_gas_mark(mark)
    if m not in GAS_MARKS:
        raise ValueError(f"Gas mark {mark!r} is not standard. Known: {sorted(GAS_MARKS)}")
    return GAS_MARKS[m][0]


def nearest_gas_mark(celsius: float) -> dict:
    """Closest gas mark to a Celsius oven temperature."""
    mark = min(GAS_MARKS, key=lambda m: abs(GAS_MARKS[m][0] - celsius))
    c, f = GAS_MARKS[mark]
    return {"gas_mark": _fmt_mark(mark), "celsius": c, "fahrenheit": f,
            "exact": abs(c - celsius) < 1}


def _fmt_mark(m: float) -> str:
    return {0.25: "1/4", 0.5: "1/2"}.get(m, str(int(m)) if m == int(m) else str(m))


def describe(celsius: float) -> str:
    table = [
        (130, "very cool / very slow"),
        (150, "cool / slow"),
        (170, "warm"),
        (185, "moderate"),
        (210, "moderately hot"),
        (225, "hot"),
        (1e9, "very hot"),
    ]
    for ceiling, label in table:
        if celsius <= ceiling:
            return label
    return "very hot"


def fan_adjust(value: float, unit: str, to: str = "fan") -> float:
    """Convert between conventional and fan-oven temperatures (same unit out)."""
    c = to_celsius(value, unit)
    if to == "fan":
        c -= FAN_OFFSET_C
    elif to in ("conventional", "conv", "static"):
        c += FAN_OFFSET_C
    else:
        raise ValueError("`to` must be 'fan' or 'conventional'")
    return from_celsius(c, unit)


def oven(value: float, unit: str = "c") -> dict:
    """One-stop oven breakdown for a (conventional) temperature."""
    c = to_celsius(value, unit)
    return {
        "input": f"{value} {unit.upper().lstrip('°')}",
        "celsius": round(c, 1),
        "fahrenheit": round(from_celsius(c, "f"), 1),
        "gas_mark": nearest_gas_mark(c),
        "fan_celsius": round(c - FAN_OFFSET_C, 1),
        "fan_fahrenheit": round(from_celsius(c - FAN_OFFSET_C, "f"), 1),
        "description": describe(c),
    }
