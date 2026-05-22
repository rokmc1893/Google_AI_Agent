"""
test_law_api_ingester.py  ── 국가법령정보 API 연동 모듈 TDD (JSON 방식)
═══════════════════════════════════════════════════════════════════════════════

API type=JSON 응답을 기반으로 파싱·수집·저장·CLI를 모두 검증합니다.
모든 네트워크 호출은 unittest.mock으로 대체됩니다.
"""

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.law_api_ingester import APIError, LawAPIClient, LawDataIngester
from modules.rag_retriever import LegalDocument


# ─────────────────────────────────────────────────────────────────────────────
# JSON 픽스처 — API 응답 구조 (type=JSON)
# ─────────────────────────────────────────────────────────────────────────────

# 법령 검색 응답 (lawSearch.do?target=law&type=JSON)
SAMPLE_LAW_SEARCH_JSON = {
    "search": {
        "target": "law",
        "keyword": "체육시설",
        "totalCnt": 1,
        "law": [
            {
                "법령일련번호": "008468",
                "법령명한글": "체육시설의 설치 이용에 관한 법률 시행규칙",
                "법령ID": "008468",
                "소관부처명": "문화체육관광부",
                "시행일자": "20240101",
            }
        ],
    }
}

# 법령 상세 응답 (lawService.do?target=law&MST=008468&type=JSON)
SAMPLE_LAW_DETAIL_JSON = {
    "법령": {
        "기본정보": {
            "법령ID": "008468",
            "법령명_한글": "체육시설의 설치 이용에 관한 법률 시행규칙",
            "법종구분명": "시행규칙",
        },
        "조문": {
            "조문단위": [
                {
                    "조문번호": "1",
                    "조문제목": "목적",
                    "조문내용": "제1조(목적) 이 규칙은 체육시설의 설치·이용에 관한 법률 및 같은 법 시행령에서 위임된 사항을 규정함을 목적으로 한다.",
                },
                {
                    "조문번호": "2",
                    "조문제목": "정의",
                    "조문내용": "제2조(정의) 이 규칙에서 사용하는 용어의 뜻은 다음과 같다.",
                },
            ]
        },
    }
}

# 판례 검색 응답 (lawSearch.do?target=prec&type=JSON)
SAMPLE_PREC_SEARCH_JSON = {
    "search": {
        "target": "prec",
        "keyword": "비밀유지",
        "totalCnt": 1,
        "prec": [
            {
                "판례일련번호": "240583",
                "사건번호": "2023다12345",
                "법원명": "대법원",
            }
        ],
    }
}

# 판례 상세 응답 (lawService.do?target=prec&ID=240583&type=JSON)
SAMPLE_PREC_DETAIL_JSON = {
    "PrecService": {
        "판례일련번호": "240583",
        "법원명": "대법원",
        "사건번호": "2023다12345",
        "사건명": "비밀유지 의무 위반으로 인한 손해배상(기)",
        "판시사항": "비밀유지 의무의 범위에 관한 법리",
        "판결요지": "비밀유지 의무의 범위가 포괄적으로 규정되어 있어 직업 선택의 자유를 과도하게 제한하면 무효이다.",
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# LawAPIClient 초기화 및 HTTP 요청 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_api_client_initialization():
    """기본 초기화 시 api_key='test', base_url이 올바르게 설정되어야 한다."""
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {}, clear=True):
        client = LawAPIClient()
        assert client.api_key == "test"
        assert client.base_url == "https://www.law.go.kr/DRF/"

    client2 = LawAPIClient(api_key="my_key", base_url="http://example.com/api")
    assert client2.api_key == "my_key"
    assert client2.base_url == "http://example.com/api/"


@patch("urllib.request.urlopen")
def test_request_returns_parsed_json(mock_urlopen):
    """_request()가 JSON 바이트 응답을 딕셔너리로 파싱해 반환해야 한다."""
    payload = json.dumps({"search": {"totalCnt": 0}}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient(api_key="test_key")
    result = client.search_laws("민법")

    assert isinstance(result, dict)
    assert "search" in result


@patch("urllib.request.urlopen")
def test_request_url_contains_json_type(mock_urlopen):
    """요청 URL에 type=JSON 파라미터가 포함되어야 한다 (XML이 아님)."""
    payload = json.dumps({}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient(api_key="key123")
    client.search_laws("위약금")

    called_url = mock_urlopen.call_args[0][0].full_url
    assert "type=JSON" in called_url
    assert "type=XML" not in called_url
    assert "OC=key123" in called_url


@patch("urllib.request.urlopen")
def test_request_url_error_raises_api_error(mock_urlopen):
    """URLError 발생 시 APIError로 래핑되어야 한다."""
    mock_urlopen.side_effect = urllib.error.URLError("connection refused")

    client = LawAPIClient()
    with pytest.raises(APIError, match="API 네트워크 요청 실패"):
        client.search_laws("민법")


@patch("urllib.request.urlopen")
def test_request_json_decode_error_raises_api_error(mock_urlopen):
    """응답이 올바른 JSON이 아닐 때 APIError를 발생시켜야 한다."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<<not json>>"
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient()
    with pytest.raises(APIError, match="JSON 파싱 실패"):
        client.search_laws("민법")


@patch("urllib.request.urlopen")
def test_request_generic_exception_raises_api_error(mock_urlopen):
    """일반 예외 발생 시에도 APIError로 래핑되어야 한다."""
    mock_urlopen.side_effect = Exception("unexpected error")

    client = LawAPIClient()
    with pytest.raises(APIError, match="예기치 않은 오류"):
        client.search_laws("민법")


@patch("urllib.request.urlopen")
def test_search_laws_uses_correct_params(mock_urlopen):
    """search_laws()가 target=law와 query 파라미터를 URL에 포함해야 한다."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(SAMPLE_LAW_SEARCH_JSON).encode("utf-8")
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient(api_key="test_key")
    result = client.search_laws("체육시설")

    url = mock_urlopen.call_args[0][0].full_url
    assert "target=law" in url
    assert "OC=test_key" in url
    assert isinstance(result, dict)


@patch("urllib.request.urlopen")
def test_search_precedents_uses_correct_params(mock_urlopen):
    """search_precedents()가 target=prec 파라미터를 포함해야 한다."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(SAMPLE_PREC_SEARCH_JSON).encode("utf-8")
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient(api_key="test_key")
    result = client.search_precedents("비밀유지")

    url = mock_urlopen.call_args[0][0].full_url
    assert "target=prec" in url
    assert isinstance(result, dict)


@patch("urllib.request.urlopen")
def test_get_law_detail_uses_mst_param(mock_urlopen):
    """get_law_detail()이 MST 파라미터와 lawService.do 엔드포인트를 사용해야 한다."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(SAMPLE_LAW_DETAIL_JSON).encode("utf-8")
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient()
    client.get_law_detail("008468")

    url = mock_urlopen.call_args[0][0].full_url
    assert "lawService.do" in url
    assert "MST=008468" in url


@patch("urllib.request.urlopen")
def test_get_precedent_detail_uses_id_param(mock_urlopen):
    """get_precedent_detail()이 ID 파라미터를 사용해야 한다."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(SAMPLE_PREC_DETAIL_JSON).encode("utf-8")
    mock_resp.headers.get_content_charset.return_value = "utf-8"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    client = LawAPIClient()
    client.get_precedent_detail("240583")

    url = mock_urlopen.call_args[0][0].full_url
    assert "ID=240583" in url
    assert "target=prec" in url


# ─────────────────────────────────────────────────────────────────────────────
# LawDataIngester.parse_law_json() 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_law_json_returns_legal_documents():
    """parse_law_json()이 LegalDocument 리스트를 반환해야 한다."""
    docs = LawDataIngester.parse_law_json(SAMPLE_LAW_DETAIL_JSON)
    assert isinstance(docs, list)
    assert all(isinstance(d, LegalDocument) for d in docs)


def test_parse_law_json_count():
    """샘플 JSON에서 정확히 2개의 조문을 파싱해야 한다."""
    docs = LawDataIngester.parse_law_json(SAMPLE_LAW_DETAIL_JSON)
    assert len(docs) == 2


def test_parse_law_json_first_doc_fields():
    """첫 번째 조문의 id, source, source_type, tags가 올바르게 설정되어야 한다."""
    docs = LawDataIngester.parse_law_json(SAMPLE_LAW_DETAIL_JSON)
    doc1 = docs[0]

    assert doc1.id == "law_008468_제1조"
    assert "체육시설의 설치 이용에 관한 법률 시행규칙" in doc1.source
    assert "제1조" in doc1.source
    assert "(목적)" in doc1.source
    assert doc1.source_type == "statute"
    assert "목적" in doc1.tags


def test_parse_law_json_content_preserved():
    """조문 본문 텍스트가 파싱 결과에 보존되어야 한다."""
    docs = LawDataIngester.parse_law_json(SAMPLE_LAW_DETAIL_JSON)
    assert "체육시설의 설치·이용에 관한 법률" in docs[0].text


def test_parse_law_json_law_name_fallback():
    """법령명_한글 없을 때 법령명한글 키로 폴백해야 한다."""
    data = {
        "법령": {
            "기본정보": {
                "법령ID": "999999",
                "법령명한글": "폴백 테스트 법률",  # ← 법령명_한글 없음
            },
            "조문": {
                "조문단위": [{
                    "조문번호": "1",
                    "조문제목": "목적",
                    "조문내용": "폴백 테스트 내용",
                }]
            },
        }
    }
    docs = LawDataIngester.parse_law_json(data)
    assert len(docs) == 1
    assert "폴백 테스트 법률" in docs[0].source


def test_parse_law_json_single_josub_as_dict():
    """조문단위가 리스트가 아닌 단일 딕셔너리일 때도 파싱되어야 한다."""
    data = {
        "법령": {
            "기본정보": {"법령ID": "111", "법령명_한글": "단일 조문 법률"},
            "조문": {
                "조문단위": {   # ← 리스트가 아닌 dict
                    "조문번호": "1",
                    "조문제목": "목적",
                    "조문내용": "단일 조문 내용입니다.",
                }
            },
        }
    }
    docs = LawDataIngester.parse_law_json(data)
    assert len(docs) == 1


def test_parse_law_json_skips_empty_content():
    """조문내용이 없는 조문단위는 건너뛰어야 한다."""
    data = {
        "법령": {
            "기본정보": {"법령ID": "222", "법령명_한글": "빈 조문 법률"},
            "조문": {
                "조문단위": [
                    {"조문번호": "1", "조문제목": "목적", "조문내용": ""},    # 건너뜀
                    {"조문번호": "2", "조문제목": "정의", "조문내용": "유효 내용"},
                ]
            },
        }
    }
    docs = LawDataIngester.parse_law_json(data)
    assert len(docs) == 1
    assert "정의" in docs[0].source


# ─────────────────────────────────────────────────────────────────────────────
# LawDataIngester.parse_precedent_json() 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_precedent_json_returns_legal_document():
    """parse_precedent_json()이 LegalDocument 리스트를 반환해야 한다."""
    docs = LawDataIngester.parse_precedent_json(SAMPLE_PREC_DETAIL_JSON)
    assert len(docs) == 1
    assert isinstance(docs[0], LegalDocument)


def test_parse_precedent_json_fields():
    """판례 LegalDocument의 id, source, source_type이 올바르게 설정되어야 한다."""
    doc = LawDataIngester.parse_precedent_json(SAMPLE_PREC_DETAIL_JSON)[0]

    assert doc.id == "precedent_240583"
    assert doc.source == "대법원 2023다12345 판결"
    assert doc.source_type == "precedent"
    assert "비밀유지 의무의 범위가 포괄적으로 규정되어 있어" in doc.text


def test_parse_precedent_json_tags_from_case_name():
    """사건명에서 태그가 추출되어야 한다."""
    doc = LawDataIngester.parse_precedent_json(SAMPLE_PREC_DETAIL_JSON)[0]
    # "비밀유지 의무 위반으로 인한 손해배상(기)" → (기) 제거 후 분리
    assert "비밀유지" in doc.tags
    assert "손해배상" in doc.tags


def test_parse_precedent_json_fallback_to_issues():
    """판결요지가 없을 때 판시사항으로 폴백해야 한다."""
    data = {
        "PrecService": {
            "판례일련번호": "888888",
            "법원명": "서울고등법원",
            "사건번호": "2023나88888",
            "사건명": "계약 위반",
            "판시사항": "판시사항 내용입니다.",
            # 판결요지 없음
        }
    }
    docs = LawDataIngester.parse_precedent_json(data)
    assert len(docs) == 1
    assert "판시사항 내용입니다." in docs[0].text
    assert docs[0].source == "서울고등법원 2023나88888 판결"


def test_parse_precedent_json_no_text_returns_empty():
    """판결요지와 판시사항 모두 없으면 빈 리스트를 반환해야 한다."""
    data = {
        "PrecService": {
            "판례일련번호": "999999",
            "법원명": "대법원",
            "사건번호": "2024다99999",
            "사건명": "텍스트 없는 판례",
        }
    }
    docs = LawDataIngester.parse_precedent_json(data)
    assert docs == []


def test_parse_precedent_json_default_court_name():
    """법원명이 없을 때 기본값 '대법원'을 사용해야 한다."""
    data = {
        "PrecService": {
            "판례일련번호": "777777",
            "사건번호": "2024다77777",
            "판결요지": "테스트 판결 내용",
        }
    }
    docs = LawDataIngester.parse_precedent_json(data)
    assert len(docs) == 1
    assert "대법원" in docs[0].source


# ─────────────────────────────────────────────────────────────────────────────
# LawDataIngester.save_to_json_db() 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_save_to_json_db_creates_file(tmp_path):
    """존재하지 않는 경로에 DB 파일을 새로 생성해야 한다."""
    db_file = tmp_path / "subdir" / "test_db.json"
    ingester = LawDataIngester(db_file)
    doc = LegalDocument(id="law_1", source="민법 제1조", source_type="statute",
                        text="내용", tags=["태그"])
    ingester.save_to_json_db([doc])
    assert db_file.exists()


def test_save_to_json_db_upsert(tmp_path):
    """동일 id 문서는 덮어쓰기(Upsert)되어야 한다."""
    db_file = tmp_path / "test_db.json"
    ingester = LawDataIngester(db_file)

    doc1 = LegalDocument(id="law_1", source="민법 제1조", source_type="statute",
                         text="원본 내용", tags=["태그1"])
    ingester.save_to_json_db([doc1])

    doc1_updated = LegalDocument(id="law_1", source="민법 제1조", source_type="statute",
                                 text="수정된 내용", tags=["태그1", "수정"])
    doc2 = LegalDocument(id="prec_2", source="대법원 2023다2 판결",
                         source_type="precedent", text="판결 내용", tags=["태그2"])
    ingester.save_to_json_db([doc1_updated, doc2])

    with open(db_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc_dict = {d["id"]: d for d in data}
    assert len(data) == 2
    assert doc_dict["law_1"]["text"] == "수정된 내용"
    assert "수정" in doc_dict["law_1"]["tags"]
    assert doc_dict["prec_2"]["text"] == "판결 내용"


def test_save_to_json_db_corrupted_file_recovery(tmp_path):
    """기존 DB가 손상된 JSON이면 빈 리스트로 초기화 후 저장해야 한다."""
    db_file = tmp_path / "corrupted.json"
    db_file.write_text("{ 손상된 JSON }", encoding="utf-8")

    ingester = LawDataIngester(db_file)
    doc = LegalDocument(id="law_new", source="새 법령 제1조", source_type="statute",
                        text="새 내용", tags=["새"])
    ingester.save_to_json_db([doc])

    with open(db_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["id"] == "law_new"


# ─────────────────────────────────────────────────────────────────────────────
# ingest_by_search() 통합 테스트 (mock API)
# ─────────────────────────────────────────────────────────────────────────────

def test_ingest_by_search_law(tmp_path):
    """법령 검색→상세 수집→DB 저장의 전체 흐름이 동작해야 한다."""
    db_file = tmp_path / "law_db.json"
    ingester = LawDataIngester(db_file)

    mock_client = MagicMock()
    mock_client.search_laws.return_value = SAMPLE_LAW_SEARCH_JSON
    mock_client.get_law_detail.return_value = SAMPLE_LAW_DETAIL_JSON

    docs = ingester.ingest_by_search("체육시설", "law", mock_client, limit=1)

    mock_client.search_laws.assert_called_once_with("체육시설")
    mock_client.get_law_detail.assert_called_once_with("008468")
    assert len(docs) == 2  # 샘플에 조문 2개

    with open(db_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2


def test_ingest_by_search_prec(tmp_path):
    """판례 검색→상세 수집→DB 저장의 전체 흐름이 동작해야 한다."""
    db_file = tmp_path / "prec_db.json"
    ingester = LawDataIngester(db_file)

    mock_client = MagicMock()
    mock_client.search_precedents.return_value = SAMPLE_PREC_SEARCH_JSON
    mock_client.get_precedent_detail.return_value = SAMPLE_PREC_DETAIL_JSON

    docs = ingester.ingest_by_search("비밀유지", "prec", mock_client, limit=1)

    mock_client.search_precedents.assert_called_once_with("비밀유지")
    mock_client.get_precedent_detail.assert_called_once_with("240583")
    assert len(docs) == 1


def test_ingest_by_search_law_partial_failure(tmp_path):
    """일부 법령 상세 수집 실패 시 나머지 결과는 반환되어야 한다."""
    db_file = tmp_path / "partial_db.json"
    ingester = LawDataIngester(db_file)

    search_json_two = {
        "search": {
            "law": [
                {"법령일련번호": "000001"},
                {"법령일련번호": "000002"},
            ]
        }
    }
    valid_detail = {
        "법령": {
            "기본정보": {"법령ID": "000001", "법령명_한글": "유효 법률"},
            "조문": {
                "조문단위": [{
                    "조문번호": "1", "조문제목": "목적", "조문내용": "유효한 내용입니다.",
                }]
            },
        }
    }

    mock_client = MagicMock()
    mock_client.search_laws.return_value = search_json_two
    mock_client.get_law_detail.side_effect = [valid_detail, APIError("두 번째 실패")]

    docs = ingester.ingest_by_search("테스트", "law", mock_client, limit=2)
    assert len(docs) == 1


def test_ingest_by_search_prec_partial_failure(tmp_path):
    """일부 판례 수집 실패 시 나머지 결과는 반환되어야 한다."""
    db_file = tmp_path / "partial_prec.json"
    ingester = LawDataIngester(db_file)

    search_json_two = {
        "search": {
            "prec": [
                {"판례일련번호": "111111"},
                {"판례일련번호": "222222"},
            ]
        }
    }
    valid_prec = {
        "PrecService": {
            "판례일련번호": "111111",
            "법원명": "대법원",
            "사건번호": "2024다11111",
            "사건명": "테스트",
            "판결요지": "유효한 판결 내용입니다.",
        }
    }

    mock_client = MagicMock()
    mock_client.search_precedents.return_value = search_json_two
    mock_client.get_precedent_detail.side_effect = [valid_prec, APIError("두 번째 판례 실패")]

    docs = ingester.ingest_by_search("테스트", "prec", mock_client, limit=2)
    assert len(docs) == 1


def test_ingest_by_search_invalid_target(tmp_path):
    """지원하지 않는 target 입력 시 ValueError가 발생해야 한다."""
    ingester = LawDataIngester(tmp_path / "db.json")
    with pytest.raises(ValueError, match="지원하지 않는 target"):
        ingester.ingest_by_search("민법", "invalid", MagicMock())


def test_ingest_by_search_search_json_parse_error(tmp_path):
    """검색 결과 JSON 구조가 예상과 다를 때 ValueError가 발생해야 한다."""
    ingester = LawDataIngester(tmp_path / "db.json")

    mock_client = MagicMock()
    # law 키가 없고 구조가 깨진 JSON
    mock_client.search_laws.return_value = {"search": None}

    with pytest.raises((ValueError, TypeError, AttributeError)):
        ingester.ingest_by_search("민법", "law", mock_client)


# ─────────────────────────────────────────────────────────────────────────────
# CLI main() 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_main_law(tmp_path, capsys):
    """CLI main()이 법령 수집 흐름을 완료하고 완료 메시지를 출력해야 한다."""
    db_path = tmp_path / "cli_db.json"

    mock_client = MagicMock()
    mock_client.search_laws.return_value = SAMPLE_LAW_SEARCH_JSON
    mock_client.get_law_detail.return_value = SAMPLE_LAW_DETAIL_JSON

    with patch("sys.argv", [
        "law_api_ingester", "--target", "law",
        "--query", "체육시설",
        "--db-path", str(db_path),
        "--limit", "1",
    ]):
        with patch("modules.law_api_ingester.LawAPIClient", return_value=mock_client):
            from modules.law_api_ingester import main
            main()

    captured = capsys.readouterr()
    assert "수집 시작" in captured.out
    assert "완료" in captured.out


def test_cli_main_error_handling(tmp_path, capsys):
    """CLI main()에서 예외 발생 시 에러 메시지를 출력하고 종료해야 한다."""
    db_path = tmp_path / "cli_error_db.json"

    mock_client = MagicMock()
    mock_client.search_laws.side_effect = APIError("테스트 API 에러")

    with patch("sys.argv", [
        "law_api_ingester", "--target", "law",
        "--query", "에러테스트",
        "--db-path", str(db_path),
    ]):
        with patch("modules.law_api_ingester.LawAPIClient", return_value=mock_client):
            from modules.law_api_ingester import main
            main()

    captured = capsys.readouterr()
    assert "에러" in captured.out
