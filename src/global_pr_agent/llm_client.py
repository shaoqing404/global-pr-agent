from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.4
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.environ.get("LLM_API_KEY", os.environ.get("DEEPSEEK_API_KEY", "")),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("LLM_MODEL", "deepseek-chat"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.4")),
            timeout=int(os.environ.get("LLM_TIMEOUT", "60")),
        )


class LLMClient:
    """Minimal OpenAI-compatible chat completions client.

    The client intentionally has a small surface area so it can be replaced by
    Dify, Coze, n8n, a private model gateway, or any other model provider.
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self.config = config or LLMConfig.from_env()

    @property
    def available(self) -> bool:
        return bool(self.config.api_key)

    def chat(self, messages: List[Dict[str, str]], temperature: Optional[float] = None) -> Optional[str]:
        if not self.available:
            return None
        base = self.config.base_url.rstrip("/")
        url = f"{base}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature if temperature is None else temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.config.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001 - app should gracefully fall back in demos
            return f"[LLM_CALL_FAILED] {exc}"
