"""Profile data model, parsed from profile.toml.

Keys are English (neofetch convention). Values are free-form UTF-8, so
Chinese content works fine without any localisation code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class ProfileData:
    user: str
    joined_year: int
    career_start: date
    os: str
    host: str
    kernel: str
    ide: str
    hobbies: str
    programming: str
    spoken: str
    email: str
    contact_extra: dict[str, str] = field(default_factory=dict)

    @property
    def uptime(self) -> str:
        today = date.today()
        years = today.year - self.career_start.year
        months = today.month - self.career_start.month
        if months < 0:
            years -= 1
            months += 12
        parts = []
        if years:
            parts.append(f"{years} 年")
        if months:
            parts.append(f"{months} 个月")
        if not parts:
            parts.append("0 个月")
        return " ".join(parts)


def load_profile(path: Path) -> ProfileData:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    gh = raw["github"]
    career = raw["career"]
    about = raw["about"]
    langs = raw["languages"]
    contact = raw.get("contact", {})

    career_start = career["start"]
    if not isinstance(career_start, date):
        career_start = date.fromisoformat(str(career_start))

    email = contact.get("email", "")
    extra = {k: v for k, v in contact.items() if k != "email"}

    return ProfileData(
        user=gh["user"],
        joined_year=int(gh["joined_year"]),
        career_start=career_start,
        os=about.get("os", ""),
        host=about.get("host", ""),
        kernel=about.get("kernel", ""),
        ide=about.get("ide", ""),
        hobbies=about.get("hobbies", ""),
        programming=langs.get("programming", ""),
        spoken=langs.get("spoken", ""),
        email=email,
        contact_extra=extra,
    )
