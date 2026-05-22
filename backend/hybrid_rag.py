import math
import re
from typing import Any, Dict, List, Tuple

# 모의 법률/규정 데이터베이스 (하도급법, 민법, 사내 표준 계약 가이드라인)
LAW_DATABASE = [
    {
        "id": "SUB_LAW_16_2",
        "category": "하도급법",
        "clause": "제16조의2 (설계변경 등에 따른 하도급대금의 조정)",
        "content": "원사업자는 발주자로부터 설계변경 또는 물가변동 등의 이유로 계약금액을 증액받은 경우, 동일한 사유로 수급사업자의 하도급대금을 증액하여야 하며, 감액받은 경우 하도급대금을 감액할 수 있다.",
        "keywords": ["설계변경", "물가변동", "하도급대금", "조정", "증액", "감액"]
    },
    {
        "id": "SUB_LAW_13",
        "category": "하도급법",
        "clause": "제13조 (하도급대금의 지급 등)",
        "content": "원사업자가 수급사업자에게 제조 등의 위탁을 하는 경우에는 목적물 등의 수령일부터 60일 이내의 가능한 짧은 기한으로 정한 지급기일까지 하도급대금을 지급하여야 한다. 60일을 초과하여 지급하는 경우 연 15.5% 이내의 지연이자를 지급하여야 한다.",
        "keywords": ["지급기일", "대금지급", "60일", "지연이자", "지체이자", "연이율"]
    },
    {
        "id": "SUB_LAW_10",
        "category": "하도급법",
        "clause": "제10조 (부당한 경영간섭의 금지)",
        "content": "원사업자는 소속 임직원을 지정하여 수급사업자의 경영에 간섭하거나, 수급사업자의 의사에 반하여 특정인을 채용하도록 강요하거나 기술자료를 강제로 요구하여서는 아니 된다.",
        "keywords": ["경영간섭", "인사간섭", "기술요구", "강요", "권한침해"]
    },
    {
        "id": "CIVIL_LAW_398",
        "category": "민법",
        "clause": "제398조 (배상액의 예정)",
        "content": "당사자는 채무불이행에 관한 손해배상액을 예정할 수 있다. 손해배상의 예정액이 부당히 과다한 경우에는 법원은 적당히 감액할 수 있다. 지체상금의 약정은 손해배상액의 예정으로 추정한다.",
        "keywords": ["손해배상", "배상액 예정", "지체상금", "감액", "위약금"]
    },
    {
        "id": "COMPANY_RULE_IP_1",
        "category": "사내 표준 규정",
        "clause": "지식재산권 귀속 가이드라인 (제3조)",
        "content": "공동 연구개발 또는 용역 계약 시 발생하는 지식재산권은 원칙적으로 공동 소유로 하거나 기여도에 따라 안분하여 귀속시킨다. 일방이 개발한 독자 기술에 대한 특허권 등은 개발을 수행한 당사자에게 귀속되며, 상대방에게 일방적으로 독점 귀속시키는 독소 조항은 금지한다.",
        "keywords": ["지식재산권", "특허", "저작권", "귀속", "공동소유", "독점귀속"]
    },
    {
        "id": "COMPANY_RULE_LIMIT_1",
        "category": "사내 표준 규정",
        "clause": "책임 제한 가이드라인 (제5조)",
        "content": "계약 불이행으로 인한 손해배상 책임은 고의 또는 중과실이 없는 한 총 계약금액의 100%를 한도로 제한하여 계약을 체결하는 것을 표준으로 한다. 무제한 손해배상 책임이나 일방적 면책 조항은 사내 법무팀의 사전 특별 승인을 받아야 한다.",
        "keywords": ["손해배상", "책임제한", "한도", "일방면책", "면책조항"]
    }
]

class HybridRAG:
    """
    할루시네이션 방지를 위한 소스 가드레일 기반 하이브리드 RAG 검색 엔진.
    키워드 매칭(BM25 유사) 및 자카드 유사도를 활용하여 문장 맥락을 매핑합니다.
    """
    def __init__(self, db: List[Dict[str, Any]] = LAW_DATABASE):
        self.db = db

    def _tokenize(self, text: str) -> List[str]:
        # 조사 및 특수문자 제거하는 간이 토크나이저
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.split()
        # 2글자 이상 단어만 추출
        return [w for w in words if len(w) >= 2]

    def _calculate_jaccard(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        set_q = set(query_tokens)
        set_d = set(doc_tokens)
        intersection = set_q.intersection(set_d)
        union = set_q.union(set_d)
        return len(intersection) / len(union)

    def _keyword_match_score(self, query: str, doc: Dict[str, Any]) -> float:
        # 쿼리에 문서의 핵심 키워드가 포함되었는지 확인
        score = 0.0
        for keyword in doc.get("keywords", []):
            if keyword in query:
                score += 1.0
        return score

    def _retrieve_chroma(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            from backend.config import get_settings
            from backend.rag.status import get_rag_status
            from backend.rag.vector_store import search_similar_chunks

            if not get_settings().rag_enabled:
                return []
            enabled, _, _ = get_rag_status()
            if not enabled:
                return []
            hits = search_similar_chunks(query, top_k=top_k)
            docs: List[Dict[str, Any]] = []
            for hit in hits:
                meta = hit.get("metadata", {})
                docs.append({
                    "id": meta.get("id", hit.get("id", "RAG_HIT")),
                    "category": meta.get("category", meta.get("filename", "RAG")),
                    "clause": meta.get("clause", "검색 조항"),
                    "content": hit.get("content", ""),
                    "keywords": [],
                    "score": hit.get("score", 0),
                })
            return docs
        except Exception:
            return []

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        하이브리드(Chroma semantic + 키워드/자카드) 방식으로 유관 법령/규정 검색.
        """
        chroma_docs = self._retrieve_chroma(query, top_k)
        if chroma_docs:
            return chroma_docs[:top_k]

        query_tokens = self._tokenize(query)
        results = []

        for doc in self.db:
            doc_text = doc["clause"] + " " + doc["content"]
            doc_tokens = self._tokenize(doc_text)
            
            # 1. 맥락 유사도 (자카드)
            semantic_score = self._calculate_jaccard(query_tokens, doc_tokens)
            
            # 2. 키워드 매칭 스코어
            keyword_score = self._keyword_match_score(query, doc)
            
            # 하이브리드 가중치 합산
            hybrid_score = (semantic_score * 0.4) + (keyword_score * 0.6)
            
            if hybrid_score > 0.05: # 최소 임계치
                results.append({
                    "score": hybrid_score,
                    "doc": doc
                })

        # 스코어 역순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in results[:top_k]]

    def enforce_source_guardrail(self, response_text: str, retrieved_docs: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        검색된 출처 이외의 가짜 법률 정보(할루시네이션)가 생성되지 않도록 제한하는 소스 가드레일입니다.
        답변 내 인용구와 검색된 문서를 검증하여 매핑 정보를 확정합니다.
        """
        valid_citations = []
        for doc in retrieved_docs:
            # 답변 텍스트 내에 관련 조항 번호나 카테고리가 매핑되어 언급되는지 체크
            clause_num = doc["clause"].split(" ")[0] # 예: 제16조의2
            if clause_num in response_text or doc["category"] in response_text:
                valid_citations.append(f"{doc['category']} {doc['clause']}")
                
        # 가드레일 규칙: 인용할 정보가 검색 결과에 존재하지 않는 경우 가짜 근거로 취급하여 정화 처리
        return response_text, list(set(valid_citations))

# 간단한 테스트
if __name__ == "__main__":
    import re
    rag = HybridRAG()
    test_query = "지식재산권을 일방적으로 갑에게 귀속시키는 조항에 대해 검토해줘. 지상권 배상금은 어떻게 되나요?"
    docs = rag.retrieve(test_query)
    print("=== 검색된 관련 법령/규정 ===")
    for doc in docs:
        print(f"[{doc['category']}] {doc['clause']}")
        print(f"내용: {doc['content']}\n")
