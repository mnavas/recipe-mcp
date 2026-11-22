"""Pan-size scaling by surface area.

To keep the same batter depth (and so a similar bake), scale a recipe by the
ratio of pan surface areas. Pan specs are compact strings in centimetres:
  "round:23"  "square:20"  "rect:23x33"
"""

from __future__ import annotations

import math
import re


def parse_pan(spec: str) -> tuple[str, float, str]:
    """Return (shape, area_cm2, label) for a pan spec like 'round:23'."""
    s = spec.strip().lower()
    if ":" not in s:
        raise ValueError("Pan spec looks like 'round:23', 'square:20' or 'rect:23x33' (cm)")
    shape, dims = (p.strip() for p in s.split(":", 1))
    if shape in ("round", "circle"):
        d = float(dims)
        return "round", math.pi * (d / 2) ** 2, f"round {d:g} cm"
    if shape in ("square",):
        a = float(dims)
        return "square", a * a, f"square {a:g} cm"
    if shape in ("rect", "rectangle", "rectangular"):
        m = re.match(r"([\d.]+)\s*[x×]\s*([\d.]+)", dims)
        if not m:
            raise ValueError("Rectangular pan looks like 'rect:23x33' (cm)")
        length, width = float(m.group(1)), float(m.group(2))
        return "rectangular", length * width, f"{length:g}x{width:g} cm"
    raise ValueError(f"Unknown pan shape {shape!r} (use round, square or rect)")


def scale_for_pan(from_pan: str, to_pan: str) -> dict:
    """Area-based scale factor to move a recipe from one pan to another."""
    _, fa, fl = parse_pan(from_pan)
    _, ta, tl = parse_pan(to_pan)
    factor = ta / fa
    return {
        "from": fl, "to": tl,
        "from_area_cm2": round(fa, 1), "to_area_cm2": round(ta, 1),
        "area_factor": round(factor, 3),
        "note": ("Multiply ingredient amounts by the area factor to keep the same "
                 "batter depth. Keep the oven temperature the same; bake time is "
                 "similar at equal depth — check a few minutes early for a larger or "
                 "shallower pan. Leavening and salt don't scale perfectly; see "
                 "scaling_caveats."),
    }
