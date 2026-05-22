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
    """LLM 클라이언트. OpenAI를 기본으로 사용하며, 실패 시 Ollama로 자동 전환합니다. Gemini는 최종 백업으로 사용됩니다."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._model = None

    @property
    def enabled(self) -> bool:
        return self.settings.llm_enabled

    def _get_model(self):
        if not self.settings.gemini_api_key.strip():
            raise LLMNotConfiguredError("GEMINI_API_KEY가 없습니다.")
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
        # 1. OpenAI 호출 시도
        if self.settings.openai_api_key.strip():
            try:
                from openai import OpenAI
                logger.info("Trying OpenAI API...")
                print("[LLMClient] OpenAI 호출 시도 중...")
                client = OpenAI(api_key=self.settings.openai_api_key.strip())
                response = client.chat.completions.create(
                    model=self.settings.openai_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    temperature=0.2,
                )
                res_text = response.choices[0].message.content
                if res_text:
                    print("[LLMClient] OpenAI 호출 성공!")
                    return res_text.strip()
            except Exception as e:
                logger.warning("OpenAI API failed, transitioning to Ollama: %s", e)
                print(f"[LLMClient] OpenAI 호출 실패 ({e}) -> Ollama로 자동 전환합니다.")

        # 2. Ollama 호출 시도
        if self.settings.ollama_base_url.strip():
            try:
                from openai import OpenAI
                logger.info("Trying Ollama API at %s...", self.settings.ollama_base_url)
                print(f"[LLMClient] Ollama 호출 시도 중 ({self.settings.ollama_model})...")
                client = OpenAI(
                    base_url=f"{self.settings.ollama_base_url.rstrip('/')}/v1",
                    api_key="ollama"
                )
                response = client.chat.completions.create(
                    model=self.settings.ollama_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    temperature=0.2,
                )
                res_text = response.choices[0].message.content
                if res_text:
                    print("[LLMClient] Ollama 호출 성공!")
                    return res_text.strip()
            except Exception as e:
                logger.warning("Ollama API failed: %s", e)
                print(f"[LLMClient] Ollama 호출 실패 ({e}).")

        # 3. Gemini 최종 백업 시도
        if self.settings.gemini_api_key.strip():
            try:
                logger.info("Trying Gemini API...")
                print("[LLMClient] Gemini 호출 시도 중...")
                model = self._get_model()
                prompt = f"{system.strip()}\n\n{user.strip()}"
                response = model.generate_content(prompt)
                text = getattr(response, "text", None) or ""
                if not text and response.candidates:
                    parts = response.candidates[0].content.parts
                    text = "".join(getattr(p, "text", "") or "" for p in parts)
                if text:
                    print("[LLMClient] Gemini 호출 성공!")
                    return text.strip()
            except Exception as e:
                logger.warning("Gemini API failed: %s", e)
                print(f"[LLMClient] Gemini 호출 실패 ({e}).")

        raise LLMNotConfiguredError("모든 LLM 호출이 실패했거나 구성되지 않았습니다.")

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
