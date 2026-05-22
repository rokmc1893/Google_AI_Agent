from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(RuntimeError):
    pass


class GeminiClient:
    """Google Gemini API 래퍼. 키 없으면 호출 전에 llm_enabled=False로 우회."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._model = None

    @property
    def enabled(self) -> bool:
        return self.settings.llm_enabled

    def _get_model(self):
        if not self.enabled:
            raise LLMNotConfiguredError("GEMINI_API_KEY가 없거나 USE_LLM=false입니다.")
        if self._model is None:
            import google.generativeai as genai

            genai.configure(api_key=self.settings.gemini_api_key.strip())
            self._model = genai.GenerativeModel(
                self.settings.gemini_model,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 8192,
                },
            )
        return self._model

    def generate_text(self, system: str, user: str) -> str:
        model = self._get_model()
        prompt = f"{system.strip()}\n\n{user.strip()}"
        response = model.generate_content(prompt)
        text = getattr(response, "text", None) or ""
        if not text and response.candidates:
            parts = response.candidates[0].content.parts
            text = "".join(getattr(p, "text", "") or "" for p in parts)
        return text.strip()

    def generate_json(self, system: str, user: str) -> dict[str, Any]:
        raw = self.generate_text(system, user)
        return _parse_json_object(raw)


def _parse_json_object(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        return json.loads(match.group())
    raise ValueError(f"LLM JSON 파싱 실패: {raw[:200]}...")


_client: GeminiClient | None = None


def get_llm_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
