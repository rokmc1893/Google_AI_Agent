import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from api.index import review_contract, ReviewRequest, TEMP_DB_PATH

# Mock get_embed_fn to return a dummy function that returns a mock list of floats
def mock_get_embed_fn():
    return lambda text: [0.1] * 384

@patch("api.index.get_embed_fn", side_effect=mock_get_embed_fn)
def test_contract_clause_accumulation_success(mock_embed, sample_contract_text, mock_llm):
    # Check current DB state
    if TEMP_DB_PATH.exists():
        try:
            with open(TEMP_DB_PATH, "r", encoding="utf-8") as f:
                initial_data = json.load(f)
        except Exception:
            initial_data = []
    else:
        initial_data = []

    # Call review contract endpoint
    req = ReviewRequest(text=sample_contract_text, filename="test_contract.docx")
    response = review_contract(req)

    assert response["success"] is True

    # Check database file
    assert TEMP_DB_PATH.exists()
    with open(TEMP_DB_PATH, "r", encoding="utf-8") as f:
        db_data = json.load(f)

    # Find the accumulated clauses for this contract
    accumulated_clauses = [
        doc for doc in db_data 
        if doc.get("source_type") == "contract_clause" and "test_contract.docx" in doc.get("source", "")
    ]
    
    assert len(accumulated_clauses) > 0, "No accumulated contract clauses found in local JSON database."
    
    # Verify the structure of accumulated document
    clause = accumulated_clauses[0]
    assert clause["id"].startswith("clause_")
    assert clause["source_type"] == "contract_clause"
    assert "제" in clause["source"]
    assert "조" in clause["source"]
    assert "제" in clause["text"]
    assert "조" in clause["text"]
    assert "contract_clause" in clause["tags"]
