"""ASCII art payload loader.

`art.json` schema (produced by tools/make_art.py):

{
  "cols": <int>, "rows": <int>,
  "char_w": <float>, "char_h": <float>,
  "cells": [
      {"x": col, "y": row, "ch": "@", "c": "#RRGGBB"},
      ...
  ]
}

Renderers only need to iterate cells and emit them at (x * char_w, y * char_h).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtCell:
    x: int
    y: int
    ch: str
    color: str


@dataclass(frozen=True)
class Art:
    cols: int
    rows: int
    char_w: float
    char_h: float
    cells: list[ArtCell]


def load_art(path: Path) -> Art:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cells = [
        ArtCell(int(c["x"]), int(c["y"]), str(c["ch"]), str(c["c"]))
        for c in raw.get("cells", [])
    ]
    return Art(
        cols=int(raw["cols"]),
        rows=int(raw["rows"]),
        char_w=float(raw["char_w"]),
        char_h=float(raw["char_h"]),
        cells=cells,
    )
