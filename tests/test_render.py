from datetime import date
from pathlib import Path

from gsy_profilecard.art import Art, ArtCell
from gsy_profilecard.layout import build_rows
from gsy_profilecard.profile import ProfileData
from gsy_profilecard.render import DARK, render_svg
from gsy_profilecard.stats import Stats


def _profile() -> ProfileData:
    return ProfileData(
        user="CarGuo",
        joined_year=2011,
        career_start=date(2012, 7, 1),
        os="macOS",
        host="Guangzhou.China",
        kernel="GDE",
        ide="AS",
        hobbies="OSS",
        programming="Dart",
        spoken="Chinese",
        email="x@example.com",
    )


def _art() -> Art:
    return Art(cols=4, rows=2, char_w=8.0, char_h=16.0, cells=[
        ArtCell(0, 0, "#", "#ffffff"),
        ArtCell(1, 1, "@", "#ff8800"),
    ])


def test_render_produces_svg_with_key_bits():
    stats = Stats(repos_public=10, repos_contributed=2, stars=100, followers=50, commits=200)
    rows = build_rows(_profile(), stats, loc_total=1000, loc_plus=1200, loc_minus=200)
    svg = render_svg(_art(), rows, DARK)
    assert svg.startswith("<svg")
    assert "CarGuo@github" in svg
    assert "Lines of Code:" in svg
    assert "1,000" in svg
    assert "GitHub Stats" in svg
    assert "#0d1117" in svg  # dark bg


def test_render_uses_raw_art_colors_and_glyphs():
    stats = Stats(repos_public=1, repos_contributed=0, stars=1, followers=1, commits=1)
    rows = build_rows(_profile(), stats, loc_total=0, loc_plus=0, loc_minus=0)
    svg = render_svg(_art(), rows, DARK)
    # ASCII art is emitted verbatim (no glyph flip / colour remap).
    assert "#ffffff" in svg
    assert "#ff8800" in svg
    assert ">#<" in svg  # glyph "#" from cell 1
    assert ">@<" in svg  # glyph "@" from cell 2
