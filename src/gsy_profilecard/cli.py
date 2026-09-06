"""CLI entry point: `python -m gsy_profilecard`.

Steps:
1. Load config + profile.
2. Fetch GitHub stats (network).
3. Walk LOC across public non-fork repos (network + git).
4. Compose Row list.
5. Render dark_mode.svg.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .art import load_art
from .config import load_config
from .github import GitHubClient
from .layout import build_rows
from .loc import walk_loc
from .profile import load_profile
from .render import DARK, render_svg
from .stats import collect_stats, list_repos_for_loc


def _log(msg: str) -> None:
    print(f"[gsy-profilecard] {msg}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gsy-profilecard")
    parser.add_argument("--root", type=Path, default=None, help="Repo root; default=auto-detect")
    parser.add_argument("--skip-loc", action="store_true", help="Skip line-of-code walk (fast smoke test)")
    parser.add_argument("--offline", action="store_true", help="Skip all network calls (uses zeros)")
    args = parser.parse_args(argv)

    cfg = load_config(args.root)
    if not cfg.any_token and not args.offline:
        _log("no ACCESS_TOKEN or GITHUB_TOKEN available; falling back to --offline")
        args.offline = True

    profile = load_profile(cfg.profile_toml)
    _log(f"profile loaded for user={profile.user}")

    if args.offline:
        from .stats import Stats

        stats = Stats(repos_public=0, repos_contributed=0, stars=0, followers=0, commits=0)
        loc_total = loc_plus = loc_minus = 0
    else:
        client = GitHubClient(cfg.any_token)
        _log("fetching GitHub stats ...")
        stats = collect_stats(client, profile.user)
        _log(
            f"repos_public={stats.repos_public} stars={stats.stars} "
            f"followers={stats.followers} commits={stats.commits} "
            f"contributed={stats.repos_contributed}"
        )
        if args.skip_loc:
            loc_total = loc_plus = loc_minus = 0
            if cfg.loc_cache.is_file():
                try:
                    cache_raw = json.loads(cfg.loc_cache.read_text(encoding="utf-8"))
                    for v in cache_raw.values():
                        loc_total += int(v.get("total", 0))
                        loc_plus += int(v.get("plus", 0))
                        loc_minus += int(v.get("minus", 0))
                    _log(f"skip-loc: reused cache totals {loc_total:,}")
                except Exception:
                    pass
        else:
            _log("walking lines-of-code across public repos (this can take a while) ...")
            repos = list_repos_for_loc(client, profile.user)
            loc_total, loc_plus, loc_minus = walk_loc(
                client=client,
                user=profile.user,
                repos=repos,
                cache_path=cfg.loc_cache,
                hmac_key=cfg.cache_hmac_key,
            )
            _log(f"loc_total={loc_total:,} plus={loc_plus:,} minus={loc_minus:,}")

    art = load_art(cfg.art_json)
    rows = build_rows(profile, stats, loc_total, loc_plus, loc_minus)

    dark_svg = render_svg(art, rows, DARK)
    cfg.dark_svg.write_text(dark_svg, encoding="utf-8")
    _log(f"wrote {cfg.dark_svg} ({len(dark_svg):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
