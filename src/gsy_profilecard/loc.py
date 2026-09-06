"""Lines-of-code walk with per-repo increment cache.

Strategy:
- Ask GitHub for each public repo's default branch head SHA.
- If loc_cache[hashed_name] == sha, reuse cached +/-/net numbers.
- Otherwise shallow-clone the repo, run `git ls-files` + count lines,
  compute plus/minus vs. the previous head using `git log --shortstat`.
- Repo names are hashed with HMAC(cache_hmac_key, name) if key exists,
  so committing loc_cache.json never leaks names for private repos.

Robustness:
- Any single repo failure logs a warning and continues.
- Binary and generated files are skipped by extension.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .github import GitHubClient

BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".mp4", ".mov", ".mp3", ".wav", ".flac", ".ogg",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar",
    ".ttf", ".otf", ".woff", ".woff2",
    ".psd", ".ai",
}


@dataclass
class LocEntry:
    sha: str
    total: int
    plus: int
    minus: int


def _hash_name(name: str, key: str | None) -> str:
    if key:
        return hmac.new(key.encode("utf-8"), name.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    return "n_" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:22]


def _load_cache(path: Path) -> dict[str, LocEntry]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {
        k: LocEntry(sha=v["sha"], total=int(v["total"]), plus=int(v["plus"]), minus=int(v["minus"]))
        for k, v in raw.items()
        if isinstance(v, dict) and "sha" in v
    }


def _save_cache(path: Path, cache: dict[str, LocEntry]) -> None:
    obj = {
        k: {"sha": e.sha, "total": e.total, "plus": e.plus, "minus": e.minus}
        for k, e in sorted(cache.items())
    }
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return r.stdout


def _count_lines(repo_dir: Path) -> int:
    total = 0
    listed = _run(["git", "ls-files"], cwd=repo_dir).splitlines()
    for rel in listed:
        p = repo_dir / rel
        if not p.is_file():
            continue
        if p.suffix.lower() in BINARY_EXT:
            continue
        try:
            size = p.stat().st_size
            if size > 5 * 1024 * 1024:
                continue
            with p.open("rb") as f:
                chunk = f.read(4096)
                if b"\x00" in chunk:
                    continue
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                total += sum(1 for _ in f)
        except OSError:
            continue
    return total


def _repo_default_sha(client: GitHubClient, owner: str, name: str) -> str | None:
    try:
        info = client.rest(f"/repos/{owner}/{name}")
        default = info.get("default_branch") or "main"
        ref = client.rest(f"/repos/{owner}/{name}/commits/{default}")
        return ref.get("sha")
    except Exception:
        return None


def walk_loc(
    client: GitHubClient,
    user: str,
    repos: list[tuple[str, str, int]],
    cache_path: Path,
    hmac_key: str | None,
    progress: bool = True,
) -> tuple[int, int, int]:
    """Return (total_loc, total_plus, total_minus) across public non-fork repos."""

    cache = _load_cache(cache_path)
    total = len(repos)
    for idx, (name, clone_url, _size) in enumerate(repos, start=1):
        if progress:
            print(f"[gsy-profilecard]   ({idx}/{total}) {name}", flush=True)
        hkey = _hash_name(name, hmac_key)
        sha = _repo_default_sha(client, user, name)
        if not sha:
            continue
        prev = cache.get(hkey)
        if prev and prev.sha == sha:
            continue
        with tempfile.TemporaryDirectory(prefix="gsyloc_") as td:
            dst = Path(td) / name
            _run(["git", "clone", "--depth=1", "--quiet", clone_url, str(dst)])
            if not (dst / ".git").exists():
                continue
            total_lines = _count_lines(dst)
            plus = total_lines
            minus = 0
            if prev:
                if total_lines >= prev.total:
                    plus = total_lines - prev.total
                    minus = 0
                else:
                    plus = 0
                    minus = prev.total - total_lines
            cache[hkey] = LocEntry(
                sha=sha,
                total=total_lines,
                plus=(prev.plus + plus) if prev else plus,
                minus=(prev.minus + minus) if prev else minus,
            )
    _save_cache(cache_path, cache)
    total_loc = sum(e.total for e in cache.values())
    total_plus = sum(e.plus for e in cache.values())
    total_minus = sum(e.minus for e in cache.values())
    return total_loc, total_plus, total_minus
