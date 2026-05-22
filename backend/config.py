from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = 10 * 1024 * 1024

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3"
    
    use_llm: bool = True

    law_api_key: str = ""
    chroma_dir: str = "backend/data/chroma"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    use_rag: bool = True
    screen_sla_seconds: int = 180
    use_langgraph: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return self.use_llm and (
            bool(self.openai_api_key.strip())
            or bool(self.ollama_base_url.strip())
            or bool(self.gemini_api_key.strip())
        )

    @property
    def langgraph_enabled(self) -> bool:
        if not self.use_langgraph:
            return False
        from backend.graph.workflow import langgraph_available

        return langgraph_available()

    @property
    def rag_enabled(self) -> bool:
        if not self.use_rag:
            return False
        from backend.rag.status import get_rag_status

        enabled, _, _ = get_rag_status()
        return enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()
