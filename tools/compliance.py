"""数据获取与输出合规约束。"""

from __future__ import annotations

from urllib.parse import urlparse

# 供 ai_context / 用户可见输出附带的合规说明
DATA_USE_NOTICE = (
    "数据来源于公开渠道或用户已配置的授权 API，仅供个人投研辅助参考，"
    "不构成投资建议；请以交易所/上市公司法定披露及官方行情为准。"
)

# 资讯正文摘要仅允许抓取以下媒体域（避免任意 URL 请求）
NEWS_ARTICLE_ALLOWED_HOSTS = frozenset({
    "eastmoney.com",
    "finance.eastmoney.com",
    "caifuhao.eastmoney.com",
    "wap.eastmoney.com",
    "emwap.eastmoney.com",
})


def is_allowed_news_article_url(url: str) -> bool:
    """仅允许已知资讯合作域，降低合规与安全风险。"""
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    host = host.lower().removeprefix("www.")
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in NEWS_ARTICLE_ALLOWED_HOSTS)
