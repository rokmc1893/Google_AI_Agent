import os
import unittest.mock as mock
import pytest
import numpy as np
from modules.db_connector import PostgresDBConnector
from modules.rag_retriever import LegalDocument

@pytest.fixture
def mock_psycopg():
    with mock.patch("modules.db_connector.psycopg2") as mock_psycopg:
        yield mock_psycopg

def test_db_connector_inactive_when_no_url(mock_psycopg):
    # URL이 없고 DATABASE_URL 환경변수도 없을 때 연결을 시도하지 않고 비활성화 상태여야 함
    with mock.patch.dict(os.environ, {}, clear=True):
        connector = PostgresDBConnector(db_url=None)
        assert connector.is_active() is False
        mock_psycopg.connect.assert_not_called()

def test_db_connector_active_and_init_db(mock_psycopg):
    mock_conn = mock.MagicMock()
    mock_cursor = mock.MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_psycopg.connect.return_value = mock_conn

    # pgvector 체크 및 embedding 컬럼 체크 반환값 Mocking
    mock_cursor.fetchone.side_effect = [
        (1,),  # has_vector_type
        None,  # has_embedding (컬럼 아직 없음)
    ]

    connector = PostgresDBConnector(db_url="postgresql://user:pass@localhost:5432/db")
    assert connector.is_active() is True
    mock_psycopg.connect.assert_called_once_with("postgresql://user:pass@localhost:5432/db")
    
    # DDL 초기화 쿼리가 올바르게 트리거되었는지 검증
    mock_cursor.execute.assert_any_call("CREATE EXTENSION IF NOT EXISTS vector;")
    mock_cursor.execute.assert_any_call("""
                    CREATE TABLE IF NOT EXISTS legal_documents (
                        id VARCHAR(100) PRIMARY KEY,
                        source VARCHAR(255) NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        text TEXT NOT NULL,
                        tags TEXT[] NOT NULL
                    );
                """)
    mock_conn.commit.assert_called()

def test_db_connector_upsert_without_embeddings(mock_psycopg):
    mock_conn = mock.MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = mock.MagicMock()
    mock_cursor.connection = mock_conn
    mock_cursor.mogrify.side_effect = lambda query, args: b"(" + b", ".join(str(a).encode('utf-8') for a in args) + b")"
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_psycopg.connect.return_value = mock_conn

    # embedding 컬럼 존재 여부 체크 시 False 반환
    mock_cursor.fetchone.return_value = None

    connector = PostgresDBConnector(db_url="postgresql://user:pass@localhost:5432/db")
    
    docs = [
        LegalDocument(id="doc1", source="source1", source_type="statute", text="text1", tags=["tag1"])
    ]
    
    connector.upsert_documents(docs)
    mock_conn.commit.assert_called()

def test_db_connector_upsert_with_embeddings(mock_psycopg):
    mock_conn = mock.MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = mock.MagicMock()
    mock_cursor.connection = mock_conn
    mock_cursor.mogrify.side_effect = lambda query, args: b"(" + b", ".join(str(a).encode('utf-8') for a in args) + b")"
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_psycopg.connect.return_value = mock_conn

    # embedding 컬럼 존재 여부 체크 시 True 반환
    mock_cursor.fetchone.return_value = (1,)

    connector = PostgresDBConnector(db_url="postgresql://user:pass@localhost:5432/db")
    
    docs = [
        LegalDocument(id="doc1", source="source1", source_type="statute", text="text1", tags=["tag1"])
    ]
    embeddings = [np.array([0.1, 0.2, 0.3])]
    
    connector.upsert_documents(docs, embeddings)
    mock_conn.commit.assert_called()

def test_db_connector_load_all_documents(mock_psycopg):
    mock_conn = mock.MagicMock()
    mock_cursor = mock.MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_psycopg.connect.return_value = mock_conn

    # DB 조회 결과 Mocking
    mock_cursor.fetchall.return_value = [
        ("doc1", "source1", "statute", "text1", ["tag1"])
    ]

    connector = PostgresDBConnector(db_url="postgresql://user:pass@localhost:5432/db")
    docs = connector.load_all_documents()
    
    assert len(docs) == 1
    assert docs[0].id == "doc1"
    assert docs[0].source == "source1"
    assert docs[0].source_type == "statute"
    assert docs[0].text == "text1"
    assert docs[0].tags == ["tag1"]
