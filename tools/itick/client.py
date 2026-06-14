"""iTick REST API 客户端（参考 https://juejin.cn/post/7450054399681036326）。"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from agents.shared.artifact import now_iso
from tools.types import ToolResult

ITICK_BASE_URL = os.getenv("ITICK_BASE_URL", "https://api.itick.org")
ITICK_TOKEN = os.getenv("ITICK_TOKEN", "")


class ITickClient:
    def __init__(self, token: str | None = None, base_url: str | None = None) -> None:
        self.token = token or ITICK_TOKEN
        self.base_url = (base_url or ITICK_BASE_URL).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict[str, str]:
        return {"accept": "application/json", "token": self.token}

    def _get(self, path: str, params: dict[str, Any]) -> ToolResult:
        if not self.configured:
            return ToolResult.failure(
                "ITICK_NOT_CONFIGURED",
                "未配置 ITICK_TOKEN，请在 .env 中申请 https://itick.org 免费 API Key",
                source="iTick",
            )

        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(url, params=params, headers=self._headers())
        except httpx.HTTPError as exc:
            return ToolResult.failure("ITICK_NETWORK", str(exc), source="iTick")

        if response.status_code != 200:
            return ToolResult.failure(
                "ITICK_HTTP",
                f"HTTP {response.status_code}: {response.text[:200]}",
                source="iTick",
            )

        payload = response.json()
        if payload.get("code") not in (0, None):
            return ToolResult.failure(
                "ITICK_API",
                str(payload.get("msg") or payload),
                source="iTick",
            )

        return ToolResult.success(
            payload.get("data") if "data" in payload else payload,
            source="iTick",
            fetched_at=now_iso(),
        )

    def get_stock_tick(self, region: str, code: str) -> ToolResult:
        return self._get("/stock/tick", {"region": region, "code": code})

    def get_stock_kline(
        self,
        region: str,
        code: str,
        *,
        k_type: int = 8,
        limit: int = 30,
    ) -> ToolResult:
        return self._get(
            "/stock/kline",
            {"region": region, "code": code, "kType": str(k_type), "limit": str(limit)},
        )

    def get_stock_info(self, region: str, code: str) -> ToolResult:
        return self._get(
            "/stock/info",
            {"type": "stock", "region": region, "code": code},
        )


_default_client: Optional[ITickClient] = None


def get_itick_client() -> ITickClient:
    global _default_client
    if _default_client is None:
        _default_client = ITickClient()
    return _default_client
