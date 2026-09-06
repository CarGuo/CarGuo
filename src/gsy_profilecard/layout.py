"""Right-hand text column layout: neofetch style key/value rows and rules.

The layout is a plain list of Row dataclasses; render.py turns them into SVG.
Every row has a `kind`:
- title:  the "user@host" header line
- rule:   a full-width separator "----"
- kv:     a key/value pair with dot-fill between them
- section: an "- <label>" section title line
- kv_pair: two kv pairs on a single row (used for stats)
- multi:  a raw pre-composed cell used for LOC's coloured numbers
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .profile import ProfileData
from .stats import Stats


@dataclass
class Row:
    kind: str
    key: str = ""
    value: str = ""
    extras: dict = field(default_factory=dict)


CONTACT_LABELS = {
    "email": "Email",
    "juejin": "Juejin",
    "zhihu": "Zhihu",
    "weibo": "Weibo",
    "twitter": "Twitter",
    "blog": "Blog",
    "github": "GitHub",
    "linkedin": "LinkedIn",
}


def _repos_value(stats: Stats) -> str:
    if stats.repos_contributed:
        return f"{stats.repos_public} (contrib {stats.repos_contributed})"
    return str(stats.repos_public)


def build_rows(profile: ProfileData, stats: Stats, loc_total: int, loc_plus: int, loc_minus: int) -> list[Row]:
    title = f"{profile.user}@github"
    rows: list[Row] = [
        Row("title", value=title),
        Row("rule"),
        Row("kv", key="Role", value=profile.kernel or "-"),
        Row("blank"),
        Row("kv", key="Languages", value=profile.programming or "-"),
        Row("blank"),
        Row("section", value="Contact"),
    ]
    for k, v in profile.contact_extra.items():
        rows.append(Row("kv", key=CONTACT_LABELS.get(k, k.capitalize()), value=v))
    rows.extend([
        Row("blank"),
        Row("section", value="GitHub Stats"),
        Row(
            "kv_pair",
            extras={
                "left_key": "Repos", "left_value": _repos_value(stats),
                "right_key": "Stars", "right_value": f"{stats.stars:,}",
            },
        ),
        Row(
            "kv_pair",
            extras={
                "left_key": "Commits", "left_value": f"{stats.commits:,}",
                "right_key": "Followers", "right_value": f"{stats.followers:,}",
            },
        ),
        Row(
            "loc",
            key="Lines of Code",
            extras={
                "total": loc_total,
                "plus": loc_plus,
                "minus": loc_minus,
            },
        ),
    ])
    return rows
