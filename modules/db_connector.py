import os
from typing import Any, List, Optional
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from modules.rag_retriever import LegalDocument

class PostgresDBConnector:
    """
    PostgreSQL / Supabase pgvector 데이터베이스 커넥터.
    DATABASE_URL 환경 변수가 활성화되어 있을 때 사용됩니다.
    """
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.conn = None
        self._is_active = False
        if self.db_url:
            self._connect()

    def _connect(self):
        try:
            self.conn = psycopg2.connect(self.db_url)
            self._is_active = True
            # 자동 데이터베이스 테이블 및 확장 스키마 생성
            self.init_db()
        except Exception as e:
            print(f"[PostgreSQL] 연결 실패: {e}")
            self.conn = None
            self._is_active = False

    def is_active(self) -> bool:
        """현재 데이터베이스 연결이 실제로 유효한지 확인합니다."""
        if not self._is_active or not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return True
        except Exception:
            self._is_active = False
            self.conn = None
            return False

    def init_db(self):
        """필요한 확장 스키마(pgvector) 및 테이블을 초기화합니다."""
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                # 1. pgvector 확장 시도
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                except Exception as e:
                    print(f"[PostgreSQL] pgvector 확장을 설치하지 못했습니다 (권한 부족 혹은 미지원): {e}")
                    self.conn.rollback()
                
                # 2. 메인 법령/규정 테이블 생성
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS legal_documents (
                        id VARCHAR(100) PRIMARY KEY,
                        source VARCHAR(255) NOT NULL,
                        source_type VARCHAR(50) NOT NULL,
                        text TEXT NOT NULL,
                        tags TEXT[] NOT NULL
                    );
                """)
                
                # 3. pgvector 타입 존재 여부 확인 후 embedding 컬럼 추가
                cur.execute("SELECT 1 FROM pg_type WHERE typname = 'vector';")
                has_vector_type = cur.fetchone() is not None
                
                if has_vector_type:
                    cur.execute("""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='legal_documents' AND column_name='embedding';
                    """)
                    has_embedding = cur.fetchone() is not None
                    if not has_embedding:
                        try:
                            # pgvector 0.5.0 이상은 크기가 가변적인 vector 선언을 지원합니다.
                            cur.execute("ALTER TABLE legal_documents ADD COLUMN embedding vector;")
                        except Exception:
                            self.conn.rollback()
                            # 실패 시 범용적인 REAL[] 타입으로 추가
                            cur.execute("ALTER TABLE legal_documents ADD COLUMN embedding REAL[];")
                
                self.conn.commit()
        except Exception as e:
            print(f"[PostgreSQL] 초기화 에러: {e}")
            if self.conn:
                self.conn.rollback()

    def upsert_documents(self, documents: List[LegalDocument], embeddings: Optional[List[np.ndarray]] = None):
        """법령 문서 목록을 데이터베이스에 Upsert합니다. 입력 데이터 내 중복 ID를 제거하여 DB 충돌을 방지합니다."""
        if not self.is_active():
            raise RuntimeError("PostgreSQL 데이터베이스 연결이 활성화되어 있지 않습니다.")
        
        # 1. 단일 배치 쿼리 내 동일 ID 중복 전송으로 인한 PostgreSQL 에러 방지
        seen_ids = set()
        unique_docs = []
        unique_embs = []
        
        for i, doc in enumerate(documents):
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                unique_docs.append(doc)
                if embeddings and len(embeddings) == len(documents):
                    unique_embs.append(embeddings[i])
        
        documents = unique_docs
        embeddings = unique_embs if (embeddings and len(embeddings) == len(documents)) else None

        with self.conn.cursor() as cur:
            # embedding 컬럼 존재 여부 동적 체크
            cur.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='legal_documents' AND column_name='embedding';
            """)
            has_embedding = cur.fetchone() is not None
            
            if has_embedding and embeddings and len(embeddings) == len(documents):
                data = [
                    (
                        doc.id,
                        doc.source,
                        doc.source_type,
                        doc.text,
                        doc.tags,
                        emb.tolist() if hasattr(emb, "tolist") else list(emb)
                    )
                    for doc, emb in zip(documents, embeddings)
                ]
                query = """
                    INSERT INTO legal_documents (id, source, source_type, text, tags, embedding)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        source = EXCLUDED.source,
                        source_type = EXCLUDED.source_type,
                        text = EXCLUDED.text,
                        tags = EXCLUDED.tags,
                        embedding = EXCLUDED.embedding;
                """
                execute_values(cur, query, data)
            else:
                data = [
                    (
                        doc.id,
                        doc.source,
                        doc.source_type,
                        doc.text,
                        doc.tags
                    )
                    for doc in documents
                ]
                query = """
                    INSERT INTO legal_documents (id, source, source_type, text, tags)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        source = EXCLUDED.source,
                        source_type = EXCLUDED.source_type,
                        text = EXCLUDED.text,
                        tags = EXCLUDED.tags;
                """
                execute_values(cur, query, data)
            self.conn.commit()

    def load_all_documents(self) -> List[LegalDocument]:
        """데이터베이스에서 모든 법령 문서를 로드하여 반환합니다."""
        if not self.is_active():
            raise RuntimeError("PostgreSQL 데이터베이스 연결이 활성화되어 있지 않습니다.")
        
        documents = []
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, source, source_type, text, tags FROM legal_documents;")
            rows = cur.fetchall()
            for r in rows:
                documents.append(
                    LegalDocument(
                        id=r[0],
                        source=r[1],
                        source_type=r[2],
                        text=r[3],
                        tags=list(r[4])
                    )
                )
        return documents

    def clear_database(self):
        """데이터베이스의 모든 법령 문서를 비웁니다 (쓰레기 데이터 삭제용)."""
        if not self.is_active():
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE legal_documents;")
            self.conn.commit()
            print("[PostgreSQL] 법령 데이터베이스 테이블을 비웠습니다.")
        except Exception as e:
            print(f"[PostgreSQL] 테이블 비우기 오류: {e}")
            if self.conn:
                self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self._is_active = False
