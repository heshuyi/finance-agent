"""爬虫公共 HTTP 配置。"""

from __future__ import annotations

import os

import httpx

DEFAULT_HEADERS = {
    "User-Agent": os.getenv(
        "NEWS_CRAWLER_USER_AGENT",
        "Mozilla/5.0 (compatible; FinTeamBot/1.0; +https://github.com/finteam)",
    ),
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

CRAWLER_TIMEOUT = float(os.getenv("NEWS_CRAWLER_TIMEOUT", "15"))
CRAWLER_ENABLED = os.getenv("NEWS_CRAWLER_ENABLED", "true").lower() in {"1", "true", "yes"}
FETCH_DIGEST = os.getenv("NEWS_FETCH_DIGEST", "true").lower() in {"1", "true", "yes"}
DIGEST_LIMIT = int(os.getenv("NEWS_DIGEST_LIMIT", "2"))


def crawler_client() -> httpx.Client:
    return httpx.Client(timeout=CRAWLER_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True)
