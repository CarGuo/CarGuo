from datetime import date

from gsy_profilecard.layout import build_rows
from gsy_profilecard.profile import ProfileData
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
        contact_extra={"juejin": "j.cn/u/1"},
    )


def test_build_rows_shape():
    stats = Stats(repos_public=10, repos_contributed=2, stars=100, followers=50, commits=200)
    rows = build_rows(_profile(), stats, loc_total=1000, loc_plus=1200, loc_minus=200)
    kinds = [r.kind for r in rows]
    assert kinds[0] == "title"
    assert "section" in kinds
    assert "loc" in kinds
    assert "kv_pair" in kinds
    kv_pair_rows = [r for r in rows if r.kind == "kv_pair"]
    assert len(kv_pair_rows) == 2
    assert "10 (contrib 2)" in kv_pair_rows[0].extras["left_value"]
    assert kv_pair_rows[0].extras["right_key"] == "Stars"
