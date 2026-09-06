"""Tiny GitHub REST + GraphQL client. stdlib only.

Handles token auth, JSON decoding, basic retry on 5xx/429.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

REST = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
UA = "gsy-profilecard/1.0 (+https://github.com/CarGuo/CarGuo)"


class GitHubClient:
    def __init__(self, token: str | None, timeout: float = 30.0):
        self.token = token
        self.timeout = timeout

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "Accept": "application/vnd.github+json",
            "User-Agent": UA,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extra:
            h.update(extra)
        return h

    def _open(self, req: urllib.request.Request, retries: int = 3) -> bytes:
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (403, 429, 500, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
            except urllib.error.URLError as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        if last_err:
            raise last_err
        raise RuntimeError("unreachable")

    def rest(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = REST + path
        if params:
            from urllib.parse import urlencode

            url = f"{url}?{urlencode(params)}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        return json.loads(self._open(req).decode("utf-8"))

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> Any:
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        req = urllib.request.Request(
            GRAPHQL,
            data=payload,
            headers=self._headers({"Content-Type": "application/json"}),
            method="POST",
        )
        return json.loads(self._open(req).decode("utf-8"))
