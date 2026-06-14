"""LLM 工厂 — 默认 Google Gemini，可选 OpenAI 兼容接口。"""

from __future__ import annotations

import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel


def llm_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"))


def get_chat_model(*, temperature: float = 0.3) -> Optional[BaseChatModel]:
    """优先 GEMINI_API_KEY，其次 OPENAI_API_KEY。"""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_api_key=gemini_key,
            temperature=temperature,
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI

        kwargs: dict = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": openai_key,
            "temperature": temperature,
        }
        if base_url := os.getenv("OPENAI_BASE_URL"):
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    return None


def llm_provider_label() -> str:
    if os.getenv("GEMINI_API_KEY"):
        return f"Gemini ({os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')})"
    if os.getenv("OPENAI_API_KEY"):
        return f"OpenAI ({os.getenv('OPENAI_MODEL', 'gpt-4o-mini')})"
    return "未配置"
