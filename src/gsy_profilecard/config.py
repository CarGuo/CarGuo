"""Environment / path / token configuration.

Order of precedence for tokens:
1. Real environment variable (ACCESS_TOKEN / GITHUB_TOKEN).
2. Local `.env` file next to profile.toml (dotenv-lite: KEY=value per line).
3. Fallback `env.txt` one directory above the repo (project root),
   which is where the developer puts the token during local iteration.
4. If the file contains a single non-empty line with no `=`, treat it as ACCESS_TOKEN.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    profile_toml: Path
    art_json: Path
    loc_cache: Path
    dark_svg: Path
    access_token: str | None
    github_token: str | None
    cache_hmac_key: str | None

    @property
    def any_token(self) -> str | None:
        return self.access_token or self.github_token


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data: dict[str, str] = {}
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return data
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            if "ACCESS_TOKEN" not in data:
                data["ACCESS_TOKEN"] = line
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_config(root: Path | None = None) -> Config:
    root = (root or Path(__file__).resolve().parents[2]).resolve()
    dotenv_here = _parse_dotenv(root / ".env")
    env_txt_parent = _parse_dotenv(root.parent / "env.txt")

    def pick(key: str) -> str | None:
        return (
            os.environ.get(key)
            or dotenv_here.get(key)
            or env_txt_parent.get(key)
            or None
        )

    return Config(
        root=root,
        profile_toml=root / "profile.toml",
        art_json=root / "art.json",
        loc_cache=root / "loc_cache.json",
        dark_svg=root / "dark_mode.svg",
        access_token=pick("ACCESS_TOKEN"),
        github_token=pick("GITHUB_TOKEN"),
        cache_hmac_key=pick("CACHE_HMAC_KEY"),
    )
