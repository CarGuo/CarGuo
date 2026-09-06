from datetime import date
from pathlib import Path
import pytest

from gsy_profilecard.profile import load_profile, ProfileData


def test_load_profile(tmp_path: Path):
    p = tmp_path / "profile.toml"
    p.write_text(
        """
[github]
user = "CarGuo"
joined_year = 2011

[career]
start = 2012-07-01

[about]
os = "macOS"
host = "Guangzhou.China"
kernel = "GDE"
ide = "AS"
hobbies = "opensource"

[languages]
programming = "Dart"
spoken = "Chinese"

[contact]
email = "x@example.com"
juejin = "juejin.cn/user/1"
""",
        encoding="utf-8",
    )
    pd = load_profile(p)
    assert isinstance(pd, ProfileData)
    assert pd.user == "CarGuo"
    assert pd.joined_year == 2011
    assert pd.career_start == date(2012, 7, 1)
    assert pd.os == "macOS"
    assert pd.email == "x@example.com"
    assert pd.contact_extra == {"juejin": "juejin.cn/user/1"}


def test_uptime_never_negative(tmp_path: Path):
    p = tmp_path / "profile.toml"
    p.write_text(
        """
[github]
user = "u"
joined_year = 2100
[career]
start = 2100-01-01
[about]
os = ""
host = ""
kernel = ""
ide = ""
hobbies = ""
[languages]
programming = ""
spoken = ""
[contact]
email = ""
""",
        encoding="utf-8",
    )
    pd = load_profile(p)
    assert pd.uptime  # not empty
