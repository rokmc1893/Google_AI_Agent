# -*- coding: utf-8 -*-
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Ensure environment variables are set for the test
os.environ["OPENAI_API_KEY"] = "mock-openai-key"
os.environ["LLM_MODE"] = "openai"

from api.index import app
from run_review import llm_screening

@pytest.fixture
def client():
    return TestClient(app)

def test_api_review_openai_fallback_to_ollama_success(client):
    """
    Test that if OpenAI raises a quota error, the API fallback to Ollama works
    and successfully reviews the contract.
    """
    # Create two different mock ChatOpenAI objects
    mock_openai = MagicMock()
    # Mocking OpenAI to throw a quota exceeded error on invoke
    mock_openai.invoke.side_effect = Exception("insufficient_quota: Quota exceeded (429)")

    mock_ollama = MagicMock()
    # Mocking Ollama to return a valid response
    # For screening, it returns a list of issues
    # For reporting, it returns a report summary and recommendations
    mock_ollama.invoke.side_effect = [
        MagicMock(content="1. 제3조 제1항: 위약금 20% - 위험도 높음"),  # screening response
        MagicMock(content="[요약]\n본 계약서는 위험 조항이 포함되어 있습니다.\n\n[권고사항]\n- 제3조 제1항: 위약금 감액을 권고합니다.")  # reporting response
    ]

    # Patch ChatOpenAI creation
    # The first two calls (for screening and reporting) will return mock_openai
    # The next calls (after fallback triggers) will return mock_ollama
    call_count = 0
    def chat_openai_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if "base_url" in kwargs and "ollama" in kwargs.get("api_key", ""):
            return mock_ollama
        return mock_openai

    with patch("langchain_openai.ChatOpenAI", side_effect=chat_openai_side_effect):
        response = client.post(
            "/api/review",
            json={
                "text": "제1조 (목적) 이 계약은... 제3조 (위약금) 을은 계약을 불이행할 시 병에게 위약금 20%를 지급한다.",
                "filename": "test_contract.docx"
            }
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # Verify it successfully used Ollama outputs
        assert "위약금 감액" in str(json_data["report"])
        assert "로컬 키워드 매칭 폴백 모드" not in json_data["report"]["summary"]

def test_api_review_openai_and_ollama_fail_fallback_to_keywords(client):
    """
    Test that if both OpenAI and Ollama fail, it falls back to keyword-based screening.
    """
    mock_openai = MagicMock()
    mock_openai.invoke.side_effect = Exception("insufficient_quota: Quota exceeded (429)")

    mock_ollama = MagicMock()
    mock_ollama.invoke.side_effect = Exception("Ollama connection refused (500)")

    def chat_openai_side_effect(*args, **kwargs):
        if "base_url" in kwargs and "ollama" in kwargs.get("api_key", ""):
            return mock_ollama
        return mock_openai

    with patch("langchain_openai.ChatOpenAI", side_effect=chat_openai_side_effect):
        response = client.post(
            "/api/review",
            json={
                "text": "제1조 (목적) 이 계약은... 제3조 (위약금) 을은 계약을 불이행할 시 병에게 위약금 20%를 지급한다.",
                "filename": "test_contract.docx"
            }
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        # Verify it fell back to local keyword screening
        assert "로컬 키워드 매칭 폴백 모드" in json_data["report"]["summary"]

def test_run_review_cli_fallback_to_ollama_success():
    """
    Test that the CLI tool's llm_screening falls back to Ollama when OpenAI raises quota error.
    """
    mock_openai = MagicMock()
    mock_openai.invoke.side_effect = Exception("429 rate limit exceeded")

    mock_ollama = MagicMock()
    mock_ollama.invoke.return_value = MagicMock(content="제3조 제1항 | HIGH | 위약금 비율 20% 과다 | 민법 제398조")

    def chat_openai_side_effect(*args, **kwargs):
        if "base_url" in kwargs and "ollama" in kwargs.get("api_key", ""):
            return mock_ollama
        return mock_openai

    with patch("langchain_openai.ChatOpenAI", side_effect=chat_openai_side_effect):
        results, overall = llm_screening(
            articles=[{"number": 3, "title": "위약금", "raw_text": "을은 위약금 20%를 지급한다."}],
            retrieved_clauses=[],
            api_key="mock-openai-key"
        )
        assert results is not None
        assert overall == "HIGH"
        assert results[0]["article_ref"] == "제3조 제1항"
        assert "위약금 비율 20% 과다" in results[0]["issue"]

def test_run_review_cli_and_ollama_fail_fallback_to_keywords():
    """
    Test that if both OpenAI and Ollama fail in the CLI, it returns None, None (forcing keyword fallback).
    """
    mock_openai = MagicMock()
    mock_openai.invoke.side_effect = Exception("429 rate limit exceeded")

    mock_ollama = MagicMock()
    mock_ollama.invoke.side_effect = Exception("Connection error to local Ollama")

    def chat_openai_side_effect(*args, **kwargs):
        if "base_url" in kwargs and "ollama" in kwargs.get("api_key", ""):
            return mock_ollama
        return mock_openai

    with patch("langchain_openai.ChatOpenAI", side_effect=chat_openai_side_effect):
        results, overall = llm_screening(
            articles=[{"number": 3, "title": "위약금", "raw_text": "을은 위약금 20%를 지급한다."}],
            retrieved_clauses=[],
            api_key="mock-openai-key"
        )
        assert results is None
        assert overall is None
