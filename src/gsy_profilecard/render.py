"""Palette + SVG assembly.

Layout model:
- Fixed canvas size, art at left, text column at right.
- Each right-column row is anchored between TEXT_LEFT_X and TEXT_RIGHT_X.
- Short values are right-aligned with dot-leader fill (neofetch style).
- Long values that would overlap the key fall back to left-align after the key.
- Column math uses *display width* (CJK ideographs count as 2 columns) so a
  Chinese label mixed with an ASCII value still aligns.
- Only the dark canvas is rendered; ASCII art colours are used as-is.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from xml.sax.saxutils import escape

from .art import Art
from .layout import Row


def _dwidth(s: str) -> int:
    """East Asian display width in monospaced columns."""
    return sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in s)


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    stroke: str
    fg: str
    dim: str
    accent: str
    key: str
    value: str
    section: str
    plus: str
    minus: str
    title: str


DARK = Palette(
    name="dark",
    bg="#0d1117",
    stroke="#30363d",
    fg="#c9d1d9",
    dim="#6e7681",
    accent="#f0883e",
    key="#ff7b72",
    value="#c9d1d9",
    section="#79c0ff",
    plus="#3fb950",
    minus="#f85149",
    title="#c9d1d9",
)


FONT_STACK = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"
FONT_SIZE = 13.0
LINE_HEIGHT = 20.0
CHAR_W = FONT_SIZE * 0.6  # monospaced advance for common monospaced fonts

CANVAS_W = 960
CANVAS_H = 520
PADDING = 20

ART_X = PADDING
ART_Y = PADDING

TEXT_LEFT_X = 430
TEXT_RIGHT_X = CANVAS_W - PADDING
TEXT_START_Y = PADDING + 22

TEXT_WIDTH_PX = TEXT_RIGHT_X - TEXT_LEFT_X
TEXT_WIDTH_CHARS = int(TEXT_WIDTH_PX / CHAR_W)


def _t(x: float, y: float, text: str, color: str, weight: str = "400") -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{color}" '
        f'font-family="{FONT_STACK}" font-size="{FONT_SIZE}" '
        f'font-weight="{weight}" xml:space="preserve">{escape(text)}</text>'
    )


def _render_art(art: Art, x0: int, y0: int, palette: Palette) -> str:
    parts: list[str] = []
    for c in art.cells:
        px = x0 + c.x * art.char_w
        py = y0 + (c.y + 1) * art.char_h - 2
        parts.append(_t(px, py, c.ch, c.color))
    return "\n".join(parts)


def _kv_row(key: str, value: str, pal: Palette, y: float) -> str:
    """Render one `key: dots value` row that always fits within TEXT_WIDTH_CHARS."""
    key_text = key + ":"
    key_cols = _dwidth(key_text)
    value_cols = _dwidth(value)
    min_gap = 2

    parts = [_t(TEXT_LEFT_X, y, key_text, pal.key)]

    if key_cols + min_gap + value_cols <= TEXT_WIDTH_CHARS:
        dot_start_col = key_cols + 1
        value_start_col = TEXT_WIDTH_CHARS - value_cols
        dots_len = max(0, value_start_col - dot_start_col - 1)
        if dots_len > 0:
            parts.append(_t(TEXT_LEFT_X + dot_start_col * CHAR_W, y, "." * dots_len, pal.dim))
        parts.append(_t(TEXT_LEFT_X + value_start_col * CHAR_W, y, value, pal.value))
    else:
        parts.append(_t(TEXT_LEFT_X + (key_cols + 1) * CHAR_W, y, value, pal.value))
    return "\n".join(parts)


def _kv_pair_row(row: Row, pal: Palette, y: float) -> str:
    e = row.extras
    lk, lv = e["left_key"], str(e["left_value"])
    rk, rv = e["right_key"], str(e["right_value"])

    half_cols = TEXT_WIDTH_CHARS // 2

    lk_text = lk + ":"
    l_value_col = half_cols - _dwidth(lv) - 2
    l_dots_col = _dwidth(lk_text) + 1
    l_dots_len = max(1, l_value_col - l_dots_col)

    r_start_col = half_cols
    rk_text = "|  " + rk + ":"
    r_value_col = TEXT_WIDTH_CHARS - _dwidth(rv)
    r_dots_col = r_start_col + _dwidth(rk_text) + 1
    r_dots_len = max(1, r_value_col - r_dots_col - 1)

    parts = [
        _t(TEXT_LEFT_X, y, lk_text, pal.key),
        _t(TEXT_LEFT_X + l_dots_col * CHAR_W, y, "." * l_dots_len, pal.dim),
        _t(TEXT_LEFT_X + l_value_col * CHAR_W, y, lv, pal.value),
        _t(TEXT_LEFT_X + r_start_col * CHAR_W, y, rk_text, pal.key),
        _t(TEXT_LEFT_X + r_dots_col * CHAR_W, y, "." * r_dots_len, pal.dim),
        _t(TEXT_LEFT_X + r_value_col * CHAR_W, y, rv, pal.value),
    ]
    return "\n".join(parts)


def _loc_row(row: Row, pal: Palette, y: float) -> str:
    e = row.extras
    total = f"{int(e['total']):,}"
    plus = f"{int(e['plus']):,}++"
    minus = f"{int(e['minus']):,}--"

    label = row.key + ":" if row.key else "Lines of Code:"
    col = 0
    parts = [_t(TEXT_LEFT_X, y, label, pal.key)]
    col += _dwidth(label) + 1
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, total, pal.value))
    col += _dwidth(total)
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, "  ( ", pal.dim))
    col += 4
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, plus, pal.plus))
    col += _dwidth(plus)
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, ", ", pal.dim))
    col += 2
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, minus, pal.minus))
    col += _dwidth(minus)
    parts.append(_t(TEXT_LEFT_X + col * CHAR_W, y, " )", pal.dim))
    return "\n".join(parts)


def _render_rows(rows: list[Row], pal: Palette) -> str:
    parts: list[str] = []
    y = TEXT_START_Y
    for row in rows:
        if row.kind == "title":
            text = row.value
            parts.append(_t(TEXT_LEFT_X, y, text, pal.title, weight="600"))
            tail_start_col = _dwidth(text) + 1
            tail_len = max(1, TEXT_WIDTH_CHARS - tail_start_col)
            parts.append(_t(TEXT_LEFT_X + tail_start_col * CHAR_W, y, "-" * tail_len, pal.dim))
        elif row.kind == "rule":
            parts.append(_t(TEXT_LEFT_X, y, "-" * TEXT_WIDTH_CHARS, pal.dim))
        elif row.kind == "blank":
            pass
        elif row.kind == "section":
            parts.append(_t(TEXT_LEFT_X, y, f"— {row.value}", pal.section, weight="600"))
        elif row.kind == "kv":
            parts.append(_kv_row(row.key, row.value or "-", pal, y))
        elif row.kind == "kv_pair":
            parts.append(_kv_pair_row(row, pal, y))
        elif row.kind == "loc":
            parts.append(_loc_row(row, pal, y))
        y += LINE_HEIGHT
    return "\n".join(parts)


def render_svg(art: Art, rows: list[Row], palette: Palette) -> str:
    art_body = _render_art(art, ART_X, ART_Y, palette)
    text_body = _render_rows(rows, palette)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}" role="img" aria-label="CarGuo GitHub profile card">
  <rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" rx="10" ry="10" fill="{palette.bg}" stroke="{palette.stroke}" stroke-width="1" />
  {art_body}
  {text_body}
</svg>
"""
