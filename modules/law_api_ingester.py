"""
law_api_ingester.py  ── 국가법령정보 공동활용 API 연동 및 데이터 수집 모듈
═══════════════════════════════════════════════════════════════════════════════

이 모듈은 국가법령정보 공동활용 API(open.law.go.kr)를 활용하여 법령 및 판례 데이터를
JSON 형식으로 수집하고, 이를 LegalDocument 스키마에 맞춰 파싱하여 JSON 데이터베이스에 적재합니다.

API 응답 형식: type=JSON (기본값 변경)

법령 검색 응답 구조 (lawSearch.do?target=law&type=JSON):
{
  "search": {
    "target": "law",
    "keyword": "민법",
    "totalCnt": 10,
    "law": [
      {
        "법령일련번호": 123456,
        "법령명한글": "민법",
        "법령ID": 12345,
        ...
      }
    ]
  }
}

법령 상세 응답 구조 (lawService.do?target=law&type=JSON):
{
  "법령": {
    "기본정보": {
      "법령ID": "008468",
      "법령명_한글": "민법",
      ...
    },
    "조문": {
      "조문단위": [
        {
          "조문번호": "1",
          "조문제목": "목적",
          "조문내용": "...",
          ...
        }
      ]
    }
  }
}

판례 검색 응답 구조 (lawSearch.do?target=prec&type=JSON):
{
  "search": {
    "target": "prec",
    "prec": [
      {
        "판례일련번호": 240583,
        "사건번호": "2023다12345",
        ...
      }
    ]
  }
}

판례 상세 응답 구조 (lawService.do?target=prec&type=JSON):
{
  "PrecService": {
    "판례일련번호": "240583",
    "법원명": "대법원",
    "사건번호": "2023다12345",
    "사건명": "...",
    "판결요지": "...",
    "판시사항": "...",
    ...
  }
}
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import sys
from pathlib import Path

# 직접 실행 시 상위 디렉터리를 sys.path에 추가하여 modules 임포트가 가능하게 합니다.
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from modules.rag_retriever import LegalDocument


class APIError(Exception):
    """API 호출 또는 응답 파싱 중 발생하는 에러."""
    pass


class LawAPIClient:
    """
    국가법령정보 공동활용 API(open.law.go.kr) 클라이언트.

    인증키(OC)를 사용하여 법령/판례 목록 검색 및 상세 정보를
    JSON 형식으로 가져옵니다.

    Args:
        api_key: API 인증키(OC).
                 미제공 시 환경변수 LAW_API_KEY → LAW_OC → "test" 순서로 폴백.
        base_url: API 기본 URL.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://www.law.go.kr/DRF/",
    ):
        self.api_key = (
            api_key
            or os.getenv("LAW_API_KEY")
            or os.getenv("LAW_OC")
            or "test"
        )
        self.base_url = base_url.rstrip("/") + "/"

    # ── 내부 HTTP 요청 ────────────────────────────────────────────────────────
    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        API 엔드포인트에 GET 요청을 보내고 JSON 응답 딕셔너리를 반환합니다.

        Args:
            endpoint: API 엔드포인트 (예: "lawSearch.do")
            params: 쿼리 파라미터 딕셔너리

        Returns:
            파싱된 JSON 응답 딕셔너리

        Raises:
            APIError: 네트워크 오류 또는 JSON 파싱 실패 시
        """
        full_params = {
            "OC": self.api_key,
            "type": "JSON",   # ← XML에서 JSON으로 변경
            **params,
        }

        query_string = urllib.parse.urlencode(
            {k: str(v) for k, v in full_params.items()}
        )
        url = f"{self.base_url}{endpoint}?{query_string}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content_bytes = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                text = content_bytes.decode(charset, errors="replace")
                data = json.loads(text)
                if isinstance(data, dict) and "result" in data and not any(k in data for k in ["search", "LawSearch", "PrecSearch", "PrecService", "법령"]):
                    msg = data.get("msg", data.get("result", "API Error"))
                    raise APIError(f"국가법령정보 API 오류: {msg}")
                return data
        except urllib.error.URLError as e:
            raise APIError(f"API 네트워크 요청 실패 (URL: {url}): {e}")
        except json.JSONDecodeError as e:
            raise APIError(f"API 응답 JSON 파싱 실패: {e}")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"API 요청 중 예기치 않은 오류 발생: {e}")

    # ── 법령 검색 ─────────────────────────────────────────────────────────────
    def search_laws(self, query: str, **kwargs) -> dict[str, Any]:
        """
        법령 목록을 검색합니다. (target=law)

        Returns:
            {"search": {"law": [...], "totalCnt": N, ...}}
        """
        return self._request("lawSearch.do", {"target": "law", "query": query, **kwargs})

    def get_law_detail(self, mst: str, **kwargs) -> dict[str, Any]:
        """
        특정 법령(MST 일련번호)의 상세 내용을 가져옵니다.

        Returns:
            {"법령": {"기본정보": {...}, "조문": {"조문단위": [...]}}}
        """
        return self._request("lawService.do", {"target": "law", "MST": mst, **kwargs})

    # ── 판례 검색 ─────────────────────────────────────────────────────────────
    def search_precedents(self, query: str, **kwargs) -> dict[str, Any]:
        """
        판례 목록을 검색합니다. (target=prec)

        Returns:
            {"search": {"prec": [...], "totalCnt": N, ...}}
        """
        return self._request("lawSearch.do", {"target": "prec", "query": query, **kwargs})

    def get_precedent_detail(self, id: str, **kwargs) -> dict[str, Any]:
        """
        특정 판례(일련번호)의 상세 내용을 가져옵니다.

        Returns:
            {"PrecService": {"판례일련번호": "...", "판결요지": "...", ...}}
        """
        return self._request("lawService.do", {"target": "prec", "ID": id, **kwargs})


class LawDataIngester:
    """
    API JSON 응답을 파싱하여 LegalDocument 객체로 변환하고
    JSON 데이터베이스에 병합 적재(Upsert)하는 도구.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    # ── 법령 JSON 파싱 ────────────────────────────────────────────────────────
    @staticmethod
    def parse_law_json(json_data: dict[str, Any]) -> list[LegalDocument]:
        """
        법령 상세 JSON 응답을 파싱하여 조문 단위 LegalDocument 리스트를 반환합니다.

        Args:
            json_data: get_law_detail() 반환값
                       {"법령": {"기본정보": {...}, "조문": {"조문단위": [...]}}}

        Returns:
            조문 단위 LegalDocument 리스트

        Raises:
            ValueError: JSON 구조가 예상과 다를 때
        """
        try:
            law_root = json_data.get("법령", {})
            basic_info = law_root.get("기본정보", {})

            # 법령명 추출 (키 표기 다양성 대응)
            law_name = (
                basic_info.get("법령명_한글")
                or basic_info.get("법령명한글")
                or "알수없음"
            )
            if isinstance(law_name, str):
                law_name = law_name.strip()

            law_id = str(basic_info.get("법령ID", "unknown")).strip()

            # 조문단위: 단일 딕셔너리이면 리스트로 감싸기
            josub_raw = law_root.get("조문", {}).get("조문단위", [])
            if isinstance(josub_raw, dict):
                josub_raw = [josub_raw]

        except (AttributeError, TypeError) as e:
            raise ValueError(f"법령 JSON 구조 파싱 에러: {e}")

        documents: list[LegalDocument] = []
        for jomun in josub_raw:
            jomun_no = str(jomun.get("조문번호", "")).strip()
            if not jomun_no:
                continue

            jomun_title = str(jomun.get("조문제목", "") or "").strip()
            jomun_content = str(jomun.get("조문내용", "") or "").strip()

            if not jomun_content:
                continue

            # 조문번호 표준화: "1" → "제1조"
            if not jomun_no.startswith("제"):
                jomun_no = f"제{jomun_no}"
            if not jomun_no.endswith("조"):
                jomun_no = f"{jomun_no}조"

            # 출처 문자열 조합
            source_parts = [law_name, jomun_no]
            if jomun_title:
                fmt_title = jomun_title
                if not (fmt_title.startswith("(") and fmt_title.endswith(")")):
                    fmt_title = f"({fmt_title})"
                source_parts.append(fmt_title)
            source = " ".join(source_parts)

            # 고유 ID
            safe_no = re.sub(r"[^a-zA-Z0-9가-힣]", "", jomun_no)
            doc_id = f"law_{law_id}_{safe_no}"

            # 태그
            tags = [law_name]
            if jomun_title:
                clean = re.sub(r"[()]", "", jomun_title).strip()
                if clean:
                    tags.append(clean)

            documents.append(
                LegalDocument(
                    id=doc_id,
                    source=source,
                    source_type="statute",
                    text=jomun_content,
                    tags=tags,
                )
            )

        return documents

    # ── 판례 JSON 파싱 ────────────────────────────────────────────────────────
    @staticmethod
    def parse_precedent_json(json_data: dict[str, Any]) -> list[LegalDocument]:
        """
        판례 상세 JSON 응답을 파싱하여 LegalDocument(단일)를 반환합니다.

        Args:
            json_data: get_precedent_detail() 반환값
                       {"PrecService": {"판례일련번호": "...", "판결요지": "...", ...}}

        Returns:
            LegalDocument 리스트 (내용 없으면 빈 리스트)

        Raises:
            ValueError: JSON 구조가 예상과 다를 때
        """
        try:
            prec = json_data.get("PrecService", {})

            prec_id = str(
                prec.get("판례일련번호") or prec.get("판례ID") or "unknown"
            ).strip()
            court_name = str(prec.get("법원명") or "대법원").strip()
            case_no = str(prec.get("사건번호") or "unknown").strip()
            case_name = str(prec.get("사건명") or "").strip()
            summary = str(prec.get("판결요지") or "").strip()
            issues = str(prec.get("판시사항") or "").strip()

        except (AttributeError, TypeError) as e:
            raise ValueError(f"판례 JSON 구조 파싱 에러: {e}")

        text = summary if summary else issues
        if not text:
            return []

        source = f"{court_name} {case_no} 판결"
        doc_id = f"precedent_{prec_id}"

        # 태그: 사건명에서 괄호 제거 후 어절 분리
        tags: list[str] = []
        if case_name:
            cleaned = re.sub(r"\([^)]*\)", "", case_name)
            raw_tags = re.split(r"[,./·\s]+", cleaned)
            tags = [t.strip() for t in raw_tags if t.strip()]

        return [
            LegalDocument(
                id=doc_id,
                source=source,
                source_type="precedent",
                text=text,
                tags=tags,
            )
        ]

    # ── DB 저장 (Upsert) ──────────────────────────────────────────────────────
    def save_to_json_db(self, documents: list[LegalDocument], embeddings: list[np.ndarray] | None = None) -> None:
        """
        LegalDocument 목록을 데이터베이스에 병합 적재(Upsert)합니다.
        PostgreSQL 연결(DATABASE_URL)이 활성화되어 있으면 PostgreSQL에도 적재하며,
        기존 로컬 JSON 데이터베이스 파일에도 병행 저장합니다.
        """
        # 1. PostgreSQL 적재 시도
        try:
            from modules.db_connector import PostgresDBConnector
            pg_db = PostgresDBConnector()
            if pg_db.is_active():
                pg_db.upsert_documents(documents, embeddings)
                print(f"[PostgreSQL] {len(documents)}개 문서 적재 완료.")
        except Exception as e:
            print(f"[PostgreSQL] 적재 중 오류 발생: {e}")

        # 2. 로컬 JSON 저장
        existing_data: list[dict[str, Any]] = []
        if self.db_path.exists():
            try:
                with self.db_path.open("r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                existing_data = []

        # id 기반 중복 방지
        doc_dict = {doc["id"]: doc for doc in existing_data}
        for doc in documents:
            doc_dict[doc.id] = {
                "id": doc.id,
                "source": doc.source,
                "source_type": doc.source_type,
                "text": doc.text,
                "tags": doc.tags,
            }

        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self.db_path.open("w", encoding="utf-8") as f:
                json.dump(list(doc_dict.values()), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[JSON DB] 로컬 JSON 저장 실패 (Vercel 배포 시 무시 가능): {e}")

    # ── 단일 법령/판례 수집 ───────────────────────────────────────────────────
    def ingest_law(self, mst: str, api_client: LawAPIClient) -> list[LegalDocument]:
        """특정 법령 MST를 수집하여 DB에 저장합니다."""
        json_data = api_client.get_law_detail(mst)
        docs = self.parse_law_json(json_data)
        if docs:
            self.save_to_json_db(docs)
        return docs

    def ingest_precedent(self, id: str, api_client: LawAPIClient) -> list[LegalDocument]:
        """특정 판례 ID를 수집하여 DB에 저장합니다."""
        json_data = api_client.get_precedent_detail(id)
        docs = self.parse_precedent_json(json_data)
        if docs:
            self.save_to_json_db(docs)
        return docs

    # ── 검색 기반 일괄 수집 ───────────────────────────────────────────────────
    def ingest_by_search(
        self,
        query: str,
        target: str,
        api_client: LawAPIClient,
        limit: int = 5,
    ) -> list[LegalDocument]:
        """
        검색어와 타겟(law/prec)으로 목록 조회 후 상세 수집 및 DB 저장.

        Args:
            query: 검색 키워드 (예: "위약금", "비밀유지")
            target: "law" (법령) 또는 "prec" (판례)
            api_client: LawAPIClient 인스턴스
            limit: 최대 수집 항목 수

        Returns:
            수집된 LegalDocument 전체 목록

        Raises:
            ValueError: 지원하지 않는 target 또는 JSON 파싱 실패 시
        """
        all_docs: list[LegalDocument] = []

        if target == "law":
            search_data = api_client.search_laws(query)
            try:
                search_root = search_data.get("LawSearch") or search_data.get("search", {})
                items = search_root.get("law", [])
                if isinstance(items, dict):
                    items = [items]
                msts = [
                    str(item.get("법령일련번호", "")).strip()
                    for item in items
                    if item.get("법령일련번호")
                ][:limit]
            except (AttributeError, TypeError) as e:
                raise ValueError(f"법령 검색 결과 JSON 파싱 에러: {e}")

            for mst in msts:
                try:
                    all_docs.extend(self.ingest_law(mst, api_client))
                except Exception as e:
                    print(f"법령(MST: {mst}) 수집 중 에러 발생: {e}")

        elif target == "prec":
            search_data = api_client.search_precedents(query)
            try:
                search_root = search_data.get("PrecSearch") or search_data.get("search", {})
                items = search_root.get("prec", [])
                if isinstance(items, dict):
                    items = [items]
                ids = [
                    str(item.get("판례일련번호", "")).strip()
                    for item in items
                    if item.get("판례일련번호")
                ][:limit]
            except (AttributeError, TypeError) as e:
                raise ValueError(f"판례 검색 결과 JSON 파싱 에러: {e}")

            for pid in ids:
                try:
                    all_docs.extend(self.ingest_precedent(pid, api_client))
                except Exception as e:
                    print(f"판례(ID: {pid}) 수집 중 에러 발생: {e}")

        else:
            raise ValueError(f"지원하지 않는 target: {target}. 허용값: 'law', 'prec'")

        return all_docs


# ── CLI ────────────────────────────────────────────────────────────────────────
def main() -> None:
    """CLI 인터페이스를 활용한 일괄 수집(Batch Ingestion)."""
    import argparse

    parser = argparse.ArgumentParser(description="국가법령정보 API 수집기 CLI")
    parser.add_argument(
        "--target", required=True, choices=["law", "prec"],
        help="수집 대상 (law: 법령, prec: 판례)"
    )
    parser.add_argument("--query", required=True, help="검색 쿼리 (예: '민법', '비밀유지')")
    parser.add_argument(
        "--db-path", default="tests/fixtures/sample_legal_db.json",
        help="저장할 JSON DB 파일 경로"
    )
    parser.add_argument("--api-key", help="API 인증키(OC). 미설정 시 환경변수 또는 test 사용")
    parser.add_argument("--limit", type=int, default=5, help="수집할 항목 최대 개수")

    args = parser.parse_args()

    client = LawAPIClient(api_key=args.api_key)
    ingester = LawDataIngester(args.db_path)

    print(f"[{args.target.upper()} 수집 시작] 쿼리: '{args.query}', 저장 경로: {args.db_path}")
    try:
        docs = ingester.ingest_by_search(args.query, args.target, client, limit=args.limit)
        print(f"완료: {len(docs)}개 문서를 DB에 적재했습니다.")
    except Exception as e:
        print(f"수집 중 에러 발생: {e}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
