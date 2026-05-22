from langchain_openai import ChatOpenAI
from langchain_core import retrievers
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import tempfile
import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Dynamic System Path Insertion ──────────────────────────────────────────
# Ensure python can load modules from the parent project root or Vercel task root
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

vercel_root = Path(__file__).resolve().parent.parent
sys.path.append(str(vercel_root))

# Try importing the legalreview pipeline modules
try:
    from modules.law_api_ingester import LawAPIClient, LawDataIngester
    from modules.rag_retriever import HybridRetriever, LegalDocument, build_retriever_from_json
    from modules.agent_pipeline import LegalReviewPipeline, RiskLevel, AgentState
    from modules.masking import mask_text, unmask_text
    from modules.parser import ContractParser
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Fallback placeholders in case modules are not yet configured properly in path
    raise ImportError("Failed to load required core modules. Check PYTHONPATH or directory structure.")

app = FastAPI(title="Legal Review API Server", version="0.1.0")

# Enable CORS for all domains so the Vercel frontend can call it directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database Path Management ────────────────────────────────────────────────
# Vercel functions are read-only except for /tmp.
# We will copy the sample database to the system temp directory so it is writable.
ORIGINAL_DB_PATH = root_dir / "tests" / "fixtures" / "sample_legal_db.json"
if not ORIGINAL_DB_PATH.exists():
    ORIGINAL_DB_PATH = vercel_root / "tests" / "fixtures" / "sample_legal_db.json"
TEMP_DB_PATH = Path(tempfile.gettempdir()) / "legal_review_agent_db.json"

def init_db():
    """Initializes the writable database file in the temporary directory."""
    if not TEMP_DB_PATH.exists():
        if ORIGINAL_DB_PATH.exists():
            with open(ORIGINAL_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            with open(TEMP_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Database copied from {ORIGINAL_DB_PATH} to {TEMP_DB_PATH}")
        else:
            # Create a default empty database
            with open(TEMP_DB_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"Created new empty database at {TEMP_DB_PATH}")

init_db()

# ── Global Retriever Initialization ──────────────────────────────────────────
class EmbeddingCache:
    def __init__(self):
        # Try project root (vercel_root) first, then fallback to temp dir
        self.workspace_cache_path = vercel_root / ".embeddings_cache.json"
        self.temp_cache_path = Path(tempfile.gettempdir()) / "legal_embeddings_cache.json"
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        for path in [self.workspace_cache_path, self.temp_cache_path]:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.cache = json.load(f)
                    print(f"[EmbeddingCache] Loaded {len(self.cache)} cached embeddings.")
                    return
                except Exception as e:
                    print(f"[EmbeddingCache] Failed to load from {path}: {e}")

    def save_cache(self):
        for path in [self.workspace_cache_path, self.temp_cache_path]:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False)
                return
            except Exception as e:
                print(f"[EmbeddingCache] Failed to save to {path}: {e}")

    def get(self, text: str, model: str) -> list | None:
        import hashlib
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        key = f"{model}_{h}"
        return self.cache.get(key)

    def set(self, text: str, model: str, vector: Any):
        import hashlib
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        key = f"{model}_{h}"
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        elif isinstance(vector, np.ndarray):
            vector = list(vector)
        self.cache[key] = vector
        self.save_cache()

# Initialize global cache
_embedding_cache = EmbeddingCache()

def simple_embed(text: str) -> np.ndarray:
    """Fallback simple hash-based embedder to run locally without expensive models or APIs."""
    import hashlib
    # Use deterministic MD5 hash to avoid Python hash seed randomization issues
    h = hashlib.md5(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:4], byteorder="big") % (2**31)
    return np.random.default_rng(seed).random(384).astype(np.float32)

def deterministic_embed(text: str, dim: int = 1536) -> np.ndarray:
    import hashlib
    h = hashlib.md5(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:4], byteorder="big") % (2**31)
    return np.random.default_rng(seed).random(dim).astype(np.float32)

def get_embed_fn() -> Any:
    """Returns OpenAI embeddings if API key is present, otherwise simple embedder."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from langchain_openai import OpenAIEmbeddings
            embed_model = OpenAIEmbeddings(
                model="text-embedding-3-small", api_key=api_key
            )
            
            def safe_embed(text: str) -> list:
                # Check cache first
                cached = _embedding_cache.get(text, "openai")
                if cached is not None:
                    if len(cached) == 1536:
                        return cached
                
                try:
                    vector = embed_model.embed_query(text)
                    _embedding_cache.set(text, "openai", vector)
                    return vector
                except Exception as e:
                    print(f"[OpenAI Embedding Error] {e}. Falling back to deterministic 1536-dim vector.")
                    # Fallback to local 1536-dimensional vector without saving to cache
                    return deterministic_embed(text, 1536).tolist()
                    
            return safe_embed
        except Exception as e:
            print(f"Failed to load OpenAIEmbeddings: {e}. Falling back to simple_embed.")
            
    # Local mode embedding with cache support
    def local_embed(text: str) -> list:
        cached = _embedding_cache.get(text, "local")
        if cached is not None:
            if len(cached) == 384:
                return cached
        vector = simple_embed(text).tolist()
        _embedding_cache.set(text, "local", vector)
        return vector
        
    return local_embed

# Global retriever instance
retriever_instance: Optional[HybridRetriever] = None

def get_retriever() -> HybridRetriever:
    global retriever_instance
    if retriever_instance is None:
        try:
            from modules.db_connector import PostgresDBConnector
            pg_db = PostgresDBConnector()
            if pg_db.is_active():
                print("[PostgreSQL] 데이터베이스로부터 법령 정보를 로드하여 리트리버를 빌드합니다.")
                docs = pg_db.load_all_documents()
                if not docs and ORIGINAL_DB_PATH.exists():
                    print("[PostgreSQL] 데이터가 비어 있어 초기 Fixture 데이터를 적재합니다.")
                    with open(ORIGINAL_DB_PATH, "r", encoding="utf-8") as f:
                        fixture_data = json.load(f)
                    from modules.rag_retriever import LegalDocument
                    docs = [LegalDocument(**item) for item in fixture_data]
                    pg_db.upsert_documents(docs)
                retriever_instance = HybridRetriever(documents=docs, embed_fn=get_embed_fn())
            else:
                retriever_instance = build_retriever_from_json(TEMP_DB_PATH, get_embed_fn())
        except Exception as e:
            print(f"Error building retriever: {e}. Trying to rebuild with empty DB.")
            retriever_instance = HybridRetriever(documents=[], embed_fn=get_embed_fn())
    return retriever_instance

def reload_retriever():
    global retriever_instance
    retriever_instance = None
    get_retriever()

# ── API Models ─────────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    query: str
    target: str = "law"  # "law" or "prec"
    limit: int = 3
    mock: bool = False

class ReviewRequest(BaseModel):
    text: str
    filename: str = "직접 입력 계약서"

# ── API Endpoints ──────────────────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    """Health check endpoint showing environment details."""
    return {
        "status": "healthy",
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_law_key": bool(os.getenv("LAW_API_KEY") or os.getenv("LAW_API_KEY")),
        "db_path": str(TEMP_DB_PATH),
        "db_exists": TEMP_DB_PATH.exists()
    }

@app.get("/api/db")
def get_db_contents():
    """Returns the list of all ingested documents in the RAG database."""
    try:
        if TEMP_DB_PATH.exists():
            with open(TEMP_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database read error: {e}")

def deterministic_hash(text: str) -> int:
    import hashlib
    h = hashlib.md5(text.encode("utf-8")).digest()
    return int.from_bytes(h[:4], byteorder="big")

@app.post("/api/ingest")
def ingest_data(req: IngestRequest):
    """
    Ingests law or precedent data from the National Law Info API,
    saves it to the database, and retrains (reloads) the RAG retriever.
    """
    api_key = os.getenv("LAW_API_KEY") or os.getenv("LAW_API_KEY")
    
    # If no API key or mock flag is active, run in simulation mode
    if req.mock or not api_key:
        print(f"[Simulation Ingestion] Query: {req.query}, Target: {req.target}")
        mock_docs = []
        
        if req.target == "law":
            # Generate simulated law
            mock_id = f"law_sim_{deterministic_hash(req.query) % 1000000}_제1조"
            mock_docs.append(LegalDocument(
                id=mock_id,
                source=f"가상 {req.query}관련법 제1조",
                source_type="statute",
                text=f"제1조({req.query}의 원칙) ① 모든 계약 관계에서 {req.query} 관련 의무는 신의성실의 원칙에 따라 성실히 준수되어야 한다.",
                tags=[req.query, "가상법률"]
            ))
        else:
            # Generate simulated precedent
            mock_id = f"precedent_sim_{deterministic_hash(req.query) % 1000000}"
            mock_docs.append(LegalDocument(
                id=mock_id,
                source=f"대법원 2026다{deterministic_hash(req.query) % 99999} 판결",
                source_type="precedent",
                text=f"[판결요지] 계약 조항에 명시된 {req.query} 의무가 신의칙에 반하여 과도할 경우 그 효력은 전체 혹은 일부 무효로 간주함이 타당하다.",
                tags=[req.query, "가상판례"]
            ))
            
        ingester = LawDataIngester(TEMP_DB_PATH)
        ingester.save_to_json_db(mock_docs)
        reload_retriever()
        
        return {
            "success": True,
            "mode": "simulation",
            "message": f"Successfully ingested {len(mock_docs)} mock documents for query '{req.query}'.",
            "documents": [d.__dict__ for d in mock_docs]
        }
    
    # Real Ingestion Mode
    try:
        client = LawAPIClient(api_key=api_key)
        ingester = LawDataIngester(TEMP_DB_PATH)
        
        docs = ingester.ingest_by_search(
            query=req.query,
            target=req.target,
            api_client=client,
            limit=req.limit
        )
        
        if docs:
            reload_retriever()
            return {
                "success": True,
                "mode": "real_api",
                "message": f"Successfully ingested {len(docs)} documents from National Law API for query '{req.query}'.",
                "documents": [{
                    "id": d.id,
                    "source": d.source,
                    "source_type": d.source_type,
                    "text": d.text,
                    "tags": d.tags
                } for d in docs]
            }
        else:
            raise ValueError(f"No documents found or fetched for query '{req.query}'.")
            
    except Exception as e:
        print(f"Real API Ingest failed: {e}. Falling back to simulation mode.")
        # Fallback to mock ingest so it never blocks the UI flow completely
        mock_id = f"law_fallback_{deterministic_hash(req.query) % 1000000}_제9조"
        fallback_doc = LegalDocument(
            id=mock_id,
            source=f"폴백 {req.query}관련법 제9조",
            source_type="statute",
            text=f"제9조({req.query}관련 안전조치) ① 계약 당사자는 {req.query}에 대한 위험 요인을 감지하고 정기적 보호대책을 마련해야 한다.",
            tags=[req.query, "폴백법률"]
        )
        ingester = LawDataIngester(TEMP_DB_PATH)
        ingester.save_to_json_db([fallback_doc])
        reload_retriever()
        return {
            "success": True,
            "mode": "fallback_simulation",
            "message": f"Real API failed ({str(e)}). Ingested 1 fallback document instead.",
            "documents": [fallback_doc.__dict__]
        }
import os
print(f"로드된 API 키 확인: {os.getenv('LAW_API_KEY')}") # 여기서 본인이 설정한 변수명으로 확인
@app.post("/api/review")
def review_contract(req: ReviewRequest):
    """
    Executes the full LegalReviewPipeline:
    1. Masking sensitive names/prices.
    2. Parsing articles and paragraphs.
    3. Retrieval of matching laws/rules using HybridRetriever (RAG).
    4. Screening via LLM (or keyword fallback).
    5. Final Report creation.
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5")
        
        # Determine LLM mode: openai, ollama, or keyword (default)
        llm_mode = os.getenv("LLM_MODE", "keyword").lower()
        if openai_api_key and llm_mode == "keyword":
            llm_mode = "openai"
        elif not openai_api_key and llm_mode == "openai":
            llm_mode = "keyword"
            
        use_llm = llm_mode in ("openai", "ollama")
        
        screening_llm = None
        reporting_llm = None
        
        if use_llm:
            try:
                from langchain_openai import ChatOpenAI
                if llm_mode == "openai":
                    screening_llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        api_key=openai_api_key,
                        temperature=0
                    )
                    reporting_llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        api_key=openai_api_key,
                        temperature=0
                    )
                elif llm_mode == "ollama":
                    llm_config = {
                        "model": ollama_model,
                        "base_url": ollama_base_url,
                        "api_key": "ollama",
                        "temperature": 0
                    }
                    screening_llm = ChatOpenAI(**llm_config)
                    reporting_llm = ChatOpenAI(**llm_config)
            except Exception as e:
                print(f"Failed to initialize LLMs ({llm_mode}): {e}")
                screening_llm = None
                reporting_llm = None
                use_llm = False
                
        retriever = get_retriever() 

        pipeline = LegalReviewPipeline(
            screening_llm=screening_llm,
            reporting_llm=reporting_llm,
            retriever=retriever
        )
        
        # Build state
        state = AgentState(
            contract_text=req.text,
            masked_text=None,
            mask_mapping={},
            parsed_articles=[],
            screening_results=[],
            retrieved_clauses=[],
            risk_report=None,
            error=None,
            processing_time_seconds=0.0
        )
        
        # Exec pipeline steps
        state = pipeline.masking_node(state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        
        # Helper to initialize Ollama
        def init_ollama_llm():
            try:
                from langchain_openai import ChatOpenAI
                llm_config = {
                    "model": ollama_model,
                    "base_url": ollama_base_url,
                    "api_key": "ollama",
                    "temperature": 0
                }
                return ChatOpenAI(**llm_config)
            except Exception as e:
                print(f"Failed to initialize Ollama: {e}")
                return None

        run_keyword_screening = False

        def is_openai_error_msg(err: Optional[str]) -> bool:
            if not err:
                return False
            err_lower = err.lower()
            return any(word in err_lower for word in ["quota", "429", "rate_limit", "insufficient_quota", "apikey", "unauthorized", "api_key", "connection"])

        if not use_llm:
            # Local keyword screening mock
            run_keyword_screening = True
        else:
            if llm_mode == "openai":
                try:
                    # 1. Run screening node
                    state = pipeline.screening_node(state)
                    
                    # Check for OpenAI screening failure
                    if state.error and is_openai_error_msg(state.error):
                        print(f"[Auto-Fallback] OpenAI screening failed: {state.error}. Switching to Ollama...")
                        state.error = None
                        state.screening_results = []
                        
                        ollama_llm = init_ollama_llm()
                        if ollama_llm:
                            pipeline.screening_llm = ollama_llm
                            pipeline.reporting_llm = ollama_llm
                            state = pipeline.screening_node(state)
                        else:
                            print("[Auto-Fallback] Ollama configuration failed. Falling back to keyword matching.")
                            run_keyword_screening = True
                    
                    # 2. Run reporting node if screening didn't prompt keyword fallback
                    if not run_keyword_screening and state.error is None:
                        state = pipeline.reporting_node(state)
                        
                        # Check for OpenAI reporting failure
                        if state.error and is_openai_error_msg(state.error):
                            print(f"[Auto-Fallback] OpenAI reporting failed: {state.error}. Switching to Ollama...")
                            state.error = None
                            state.risk_report = None
                            
                            ollama_llm = init_ollama_llm()
                            if ollama_llm:
                                pipeline.screening_llm = ollama_llm
                                pipeline.reporting_llm = ollama_llm
                                state = pipeline.reporting_node(state)
                            else:
                                print("[Auto-Fallback] Ollama configuration failed. Falling back to keyword matching.")
                                run_keyword_screening = True
                    
                    if state.error is not None:
                        print(f"[Auto-Fallback] Pipeline execution failed: {state.error}. Falling back to keyword matching.")
                        run_keyword_screening = True
                        
                except Exception as run_err:
                    print(f"[Auto-Fallback] Exception during OpenAI pipeline execution: {run_err}. Switching to Ollama...")
                    state.error = None
                    state.screening_results = []
                    state.risk_report = None
                    
                    ollama_llm = init_ollama_llm()
                    if ollama_llm:
                        pipeline.screening_llm = ollama_llm
                        pipeline.reporting_llm = ollama_llm
                        
                        state = pipeline.screening_node(state)
                        if state.error is None:
                            state = pipeline.reporting_node(state)
                        
                        if state.error is not None:
                            run_keyword_screening = True
                    else:
                        run_keyword_screening = True
            else:
                # Direct Ollama execution
                state = pipeline.screening_node(state)
                if state.error is None:
                    state = pipeline.reporting_node(state)
                if state.error is not None:
                    print(f"[Auto-Fallback] Ollama execution failed: {state.error}. Falling back to keyword matching.")
                    run_keyword_screening = True

        if run_keyword_screening:
            from run_review import keyword_screening, determine_overall_risk
            keywords_res = keyword_screening(req.text, state.parsed_articles)
            overall_risk = determine_overall_risk(keywords_res)
            
            from modules.agent_pipeline import ScreeningResult, RiskReport, RiskLevel
            scr_results = [
                ScreeningResult(
                    article_ref=r["article_ref"],
                    issue_description=r["issue"],
                    risk_level=RiskLevel(r["risk_level"]),
                    relevant_clause_ids=[]
                ) for r in keywords_res
            ]
            
            sources = list({c["source"] for c in state.retrieved_clauses if c.get("source")})
            if not sources:
                sources = ["검색된 법령 없음 - 직접 법무 검토 필요"]
                
            summary = (
                f"분석 결과 계약서에서 총 {len(scr_results)}건의 위험 조항이 감지되었습니다. (로컬 키워드 매칭 폴백 모드)\n"
                f"종합 위험도 등급은 {overall_risk}입니다."
            )
            
            state.risk_report = RiskReport(
                overall_risk=RiskLevel(overall_risk),
                screening_results=scr_results,
                sources=sources,
                summary=summary,
                recommendations=["[필수] HIGH 위험 조항이 감지되었을 경우 계약 체결 전 반드시 법무팀과 협의하십시오."],
                processing_time_seconds=1.5
            )
            
        report = state.risk_report
            
        # Serialize the response
        # ==========================================
        # [최종 고도화] Serialize the response
        # ==========================================
        import re # 파일 최상단에 import re 가 없다면 추가해 주세요.
        
        mapping = state.mask_mapping if state.mask_mapping else {}

        def clean_and_unmask(text: str) -> str:
            if not text:
                return ""
            # 1. 마크다운 기호 완전히 제거
            text = re.sub(r'[*_#`]', '', text) 
            # 2. 역치환
            for mask, orig in mapping.items():
                text = text.replace(mask, orig)
            return text.strip()

        screening_serialized = []
        for r in report.screening_results:
            screening_serialized.append({
                "article_ref": r.article_ref,
                "issue_description": clean_and_unmask(r.issue_description),
                "risk_level": r.risk_level.value,
            })
            
        unmasked_recs = [clean_and_unmask(rec) for rec in (report.recommendations or [])]
        final_summary = clean_and_unmask(report.summary)

        # Accumulate parsed articles into database (isolated exceptions)
        try:
            if state.parsed_articles:
                import hashlib
                from modules.rag_retriever import LegalDocument
                from modules.law_api_ingester import LawDataIngester
                
                def get_md5_hash(text: str) -> str:
                    return hashlib.md5(text.encode("utf-8")).hexdigest()
                    
                filename = req.filename or "직접 입력 계약서"
                new_docs = []
                
                for art in state.parsed_articles:
                    art_number = art.get("number", 0)
                    art_title = art.get("title", "")
                    art_raw = art.get("raw_text", "").strip()
                    
                    clause_text = f"제{art_number}조 ({art_title})\n{art_raw}"
                    doc_id = f"clause_{get_md5_hash(filename + '_art_' + str(art_number))}"
                    
                    new_docs.append(LegalDocument(
                        id=doc_id,
                        source=f"검토 계약서: {filename} 제{art_number}조 ({art_title})",
                        source_type="contract_clause",
                        text=clause_text,
                        tags=["contract_clause", art_title]
                    ))
                
                embed_fn = get_embed_fn()
                embeddings = [np.array(embed_fn(doc.text), dtype=np.float32) for doc in new_docs]
                
                ingester = LawDataIngester(TEMP_DB_PATH)
                ingester.save_to_json_db(new_docs, embeddings)
                reload_retriever()
                print(f"[Accumulation] Successfully accumulated {len(new_docs)} clauses from contract '{filename}'.")
        except Exception as accum_err:
            print(f"[Accumulation Error] Failed to save contract clauses to database: {accum_err}")

        return {
            "success": True,
            "original_text": state.contract_text,  # ✅ 원본 텍스트 추가
            "masked_text": state.masked_text or state.contract_text,
            "report": {
                "overall_risk": report.overall_risk.value,
                "screening_results": screening_serialized,
                "sources": report.sources,
                "summary": final_summary.strip(),
                "recommendations": unmasked_recs if unmasked_recs else ["[필수] 위험 조항이 감지되었을 경우 계약 체결 전 법무팀과 협의하십시오."],
                "processing_time_seconds": round(report.processing_time_seconds, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {e}")

@app.post("/api/review/file")
async def review_file_upload(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None)
):
    """
    Accepts docx/pdf file upload, parses, masks, and reviews it.
    """
    # Temporarily set OpenAI API key if passed in form
    old_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    try:
        # Save uploaded file to temp path
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
            
        try:
            from modules.parser import parse_contract_file
            parsed = parse_contract_file(tmp_path)
            content = parsed.raw_text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File parsing error: {e}")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
                
        # Call review pipeline
        res = review_contract(ReviewRequest(text=content, filename=file.filename))
        return res
        
    finally:
        # Restore old API key
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

# ── Serve Frontend Static Files ──────────────────────────────────────────────
from fastapi.staticfiles import StaticFiles

# Try mounting the prototype build directory if it exists
build_dir = vercel_root.parent / "legal-screening-assistant-prototype-build"
if build_dir.exists():
    app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="static")
    print(f"Mounted static files from {build_dir}")

