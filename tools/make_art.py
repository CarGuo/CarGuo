"""Portrait photo → art.json.

Usage:
    python tools/make_art.py tools/avatar.png art.json [--cols 78] [--rows 22]

The output grid is what src/gsy_profilecard/art.py expects. Colors are
sampled from the source pixel; brightness selects the glyph.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


GLYPHS_DARK_TO_LIGHT = " .`',-~:;\"!i/\\|()1{}[]?+<>ntxuvczoefjLYXZOQMW#%*&$@8B"


def _load_image_rgb(path: Path):
    try:
        from PIL import Image
    except Exception as e:
        print(f"pillow is required: pip install -e '.[art]'   ({e})", file=sys.stderr)
        raise SystemExit(2)
    img = Image.open(path).convert("RGB")
    return img


def _to_grid(img, cols: int, rows: int, char_aspect: float) -> list[list[tuple[int, int, int, float]]]:
    src_w, src_h = img.size
    cell_w = src_w / cols
    cell_h = src_h / rows

    px = img.load()
    grid: list[list[tuple[int, int, int, float]]] = []
    for row in range(rows):
        line: list[tuple[int, int, int, float]] = []
        for col in range(cols):
            x0 = int(col * cell_w)
            y0 = int(row * cell_h)
            x1 = max(x0 + 1, int((col + 1) * cell_w))
            y1 = max(y0 + 1, int((row + 1) * cell_h))
            r = g = b = 0
            n = 0
            step_x = max(1, (x1 - x0) // 3)
            step_y = max(1, (y1 - y0) // 3)
            for yy in range(y0, y1, step_y):
                for xx in range(x0, x1, step_x):
                    pr, pg, pb = px[xx, yy]
                    r += pr
                    g += pg
                    b += pb
                    n += 1
            if n == 0:
                n = 1
            r //= n
            g //= n
            b //= n
            luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            line.append((r, g, b, luma))
        grid.append(line)
    return grid


def _glyph_for(luma: float) -> str:
    idx = min(int(luma * (len(GLYPHS_DARK_TO_LIGHT) - 1)), len(GLYPHS_DARK_TO_LIGHT) - 1)
    return GLYPHS_DARK_TO_LIGHT[idx]


def _boost(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = rgb
    max_c = max(r, g, b)
    if max_c == 0:
        return rgb
    scale = 255.0 / max_c
    scale = min(scale, 1.4)
    return (
        min(255, int(r * scale)),
        min(255, int(g * scale)),
        min(255, int(b * scale)),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="make_art")
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--cols", type=int, default=78)
    ap.add_argument("--rows", type=int, default=22)
    ap.add_argument("--font-size", type=float, default=14.0)
    ap.add_argument("--char-aspect", type=float, default=0.6, help="w/h ratio")
    args = ap.parse_args(argv)

    img = _load_image_rgb(args.src)
    grid = _to_grid(img, args.cols, args.rows, args.char_aspect)

    cells = []
    for y, row in enumerate(grid):
        for x, (r, g, b, luma) in enumerate(row):
            if luma < 0.08:
                continue
            r2, g2, b2 = _boost((r, g, b))
            cells.append({
                "x": x,
                "y": y,
                "ch": _glyph_for(luma),
                "c": f"#{r2:02x}{g2:02x}{b2:02x}",
            })

    payload = {
        "cols": args.cols,
        "rows": args.rows,
        "char_w": args.font_size * args.char_aspect,
        "char_h": args.font_size * 1.4285,
        "cells": cells,
    }
    args.dst.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.dst} ({len(cells)} cells, {args.cols}x{args.rows} grid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
