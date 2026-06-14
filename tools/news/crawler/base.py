"""公开数据 HTTP 客户端配置（资讯/披露接口）。"""

from __future__ import annotations

import os
import time

import httpx

DEFAULT_HEADERS = {
    "User-Agent": os.getenv(
        "NEWS_CRAWLER_USER_AGENT",
        "Mozilla/5.0 (compatible; FinTeamBot/1.0; personal-research)",
    ),
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

HTTP_TIMEOUT = float(os.getenv("DATA_HTTP_TIMEOUT", "15"))
REQUEST_INTERVAL_SEC = float(os.getenv("DATA_REQUEST_INTERVAL_SEC", "0.5"))

# 第三方资讯列表接口 — 默认开启（东财公开列表）；设为 false 可关闭
def _news_fetch_enabled() -> bool:
    return os.getenv("NEWS_FETCH_ENABLED", os.getenv("NEWS_CRAWLER_ENABLED", "true")).lower() in {
        "1", "true", "yes",
    }


NEWS_FETCH_ENABLED = _news_fetch_enabled()

# 是否抓取资讯正文页摘要 — 默认关闭，仅使用列表接口返回的标题/链接
FETCH_DIGEST = os.getenv("NEWS_FETCH_DIGEST", "false").lower() in {"1", "true", "yes"}
DIGEST_LIMIT = int(os.getenv("NEWS_DIGEST_LIMIT", "2"))

# 巨潮法定披露 — 默认开启（证监会指定信息披露平台公开接口）
FILINGS_FETCH_ENABLED = os.getenv("FILINGS_FETCH_ENABLED", "true").lower() in {"1", "true", "yes"}

_last_request_at = 0.0


def throttle_request() -> None:
    """简单限速，避免高频请求公开接口。"""
    global _last_request_at
    if REQUEST_INTERVAL_SEC <= 0:
        return
    now = time.monotonic()
    elapsed = now - _last_request_at
    if elapsed < REQUEST_INTERVAL_SEC:
        time.sleep(REQUEST_INTERVAL_SEC - elapsed)
    _last_request_at = time.monotonic()


def data_client() -> httpx.Client:
    return httpx.Client(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True)


# 兼容旧命名
crawler_client = data_client
CRAWLER_ENABLED = NEWS_FETCH_ENABLED
CRAWLER_TIMEOUT = HTTP_TIMEOUT
