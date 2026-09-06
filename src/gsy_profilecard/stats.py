"""Aggregated GitHub stats: repos, stars, followers, commits, contributed repos."""

from __future__ import annotations

from dataclasses import dataclass

from .github import GitHubClient


@dataclass(frozen=True)
class Stats:
    repos_public: int
    repos_contributed: int
    stars: int
    followers: int
    commits: int


CONTRIB_QUERY = """
query($user: String!) {
  user(login: $user) {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    repositoriesContributedTo(
      first: 1
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
      includeUserRepositories: false
    ) {
      totalCount
    }
  }
}
"""


def _list_public_repos(client: GitHubClient, user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        chunk = client.rest(
            f"/users/{user}/repos",
            params={"per_page": 100, "page": page, "type": "owner", "sort": "updated"},
        )
        if not isinstance(chunk, list) or not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return repos


def collect_stats(client: GitHubClient, user: str) -> Stats:
    user_info = client.rest(f"/users/{user}")
    followers = int(user_info.get("followers", 0))

    repos = _list_public_repos(client, user)
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos if not r.get("fork"))
    repos_public = sum(1 for r in repos if not r.get("fork"))

    commits = 0
    contributed = 0
    try:
        data = client.graphql(CONTRIB_QUERY, {"user": user})
        u = (data or {}).get("data", {}).get("user") or {}
        cc = u.get("contributionsCollection") or {}
        commits = int(cc.get("totalCommitContributions", 0)) + int(
            cc.get("restrictedContributionsCount", 0)
        )
        contributed = int((u.get("repositoriesContributedTo") or {}).get("totalCount", 0))
    except Exception:
        pass

    return Stats(
        repos_public=repos_public,
        repos_contributed=contributed,
        stars=stars,
        followers=followers,
        commits=commits,
    )


def list_repos_for_loc(client: GitHubClient, user: str) -> list[tuple[str, str, int]]:
    """Return (name, clone_url, size_kb) for each non-fork public repo."""
    repos = _list_public_repos(client, user)
    out: list[tuple[str, str, int]] = []
    for r in repos:
        if r.get("fork") or r.get("archived") or r.get("disabled"):
            continue
        name = r.get("name") or ""
        clone = r.get("clone_url") or ""
        size = int(r.get("size", 0))
        if name and clone:
            out.append((name, clone, size))
    return out
