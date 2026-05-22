"""
run_review.py  ── 계약서 위험도 분석 데모 스크립트
════════════════════════════════════════════════════════════════════

사용법:
  # OpenAI API 키 없이 (키워드 기반 분석)
  python run_review.py --file 계약서.pdf

  # OpenAI API 키 사용 (AI 기반 분석)
  python run_review.py --file 계약서.pdf --api-key sk-...

  # 보고서를 파일로 저장
  python run_review.py --file 계약서.pdf --output report.txt

지원 형식: PDF, DOCX
"""

from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

# ── ANSI 색상 (터미널 출력용) ─────────────────────────────────────────────────
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# 윈도우: stdout을 utf-8로 강제 설정 + ANSI 활성화
if sys.platform == "win32" and "pytest" not in sys.modules:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.system("")


def print_banner():
    print(f"""
{BOLD}{CYAN}========================================================
        [법무 검토 자동화 시스템] Legal Review Agent
              Contract Risk Analyzer  v0.1.0
========================================================{RESET}
""")



def print_step(step: int, total: int, msg: str):
    print(f"{BOLD}[{step}/{total}]{RESET} {msg}...", flush=True)


def print_risk_badge(level: str) -> str:
    if level == "HIGH":
        return f"{RED}{BOLD}[위험 높음 HIGH]{RESET}"
    elif level == "MEDIUM":
        return f"{YELLOW}{BOLD}[위험 중간 MEDIUM]{RESET}"
    else:
        return f"{GREEN}{BOLD}[위험 낮음 LOW]{RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# 키워드 기반 스크리닝 (LLM 없이 동작하는 폴백)
# ─────────────────────────────────────────────────────────────────────────────
RISK_RULES: list[dict[str, Any]] = [
    {
        "keywords": ["위약금", "손해배상"],
        "pattern": r"(\d+)\s*%",
        "threshold": 15,
        "risk": "HIGH",
        "article": "민법 제398조",
        "message": "위약금 비율이 과다할 가능성이 있습니다. 법원이 감액할 수 있습니다.",
    },
    {
        "keywords": ["전액 반환", "모두 반환", "전부 반환"],
        "risk": "HIGH",
        "article": "민법 제396조",
        "message": "갑의 귀책 시 전액 반환 조항은 일방적으로 불리할 수 있습니다.",
    },
    {
        "keywords": ["일방적", "갑의 재량", "갑이 결정", "갑의 판단"],
        "risk": "HIGH",
        "article": "사내규정 계약관리규정 제5조",
        "message": "일방적 계약 변경·해지 권한 조항으로 법무팀 검토가 필요합니다.",
    },
    {
        "keywords": ["비밀유지", "기밀", "영업비밀"],
        "risk": "MEDIUM",
        "article": "부정경쟁방지법 제2조 / 대법원 2023다12345",
        "message": "비밀유지 범위가 과도하게 광범위하면 무효가 될 수 있습니다.",
    },
    {
        "keywords": ["지식재산", "저작권", "특허", "모든 권리"],
        "risk": "MEDIUM",
        "article": "저작권법 제9조",
        "message": "지식재산권 귀속 조항을 명확히 확인하세요.",
    },
    {
        "keywords": ["자동 연장", "자동 갱신", "묵시적 갱신"],
        "risk": "MEDIUM",
        "article": "사내규정 계약관리규정 제12조",
        "message": "자동 연장 조항은 해지 기회를 놓칠 수 있으니 주의하세요.",
    },
    {
        "keywords": ["면책", "책임 없음", "책임을 지지"],
        "risk": "MEDIUM",
        "article": "민법 제103조",
        "message": "과도한 면책 조항은 공서양속에 반해 무효가 될 수 있습니다.",
    },
    {
        "keywords": ["경업금지", "경쟁 금지", "동종업계"],
        "risk": "MEDIUM",
        "article": "헌법 제15조 (직업선택의 자유)",
        "message": "경업금지 범위·기간이 과도하면 효력이 제한될 수 있습니다.",
    },
    {
        "keywords": ["지연이자", "연체이자", "연 %"],
        "risk": "LOW",
        "article": "이자제한법 제2조",
        "message": "법정 최고이율(연 20%)을 초과하는 이자는 무효입니다.",
    },
]


def keyword_screening(text: str, articles: list[dict]) -> list[dict]:
    """LLM 없이 키워드·패턴 기반으로 위험 조항을 탐지합니다."""
    import re
    results = []
    text_lower = text.lower()

    for rule in RISK_RULES:
        found_keywords = [kw for kw in rule["keywords"] if kw in text]
        if not found_keywords:
            continue

        # 퍼센트 패턴 임계값 체크 (위약금 규칙)
        if "pattern" in rule:
            matches = re.findall(rule["pattern"], text)
            if not matches:
                continue
            max_pct = max(int(m) for m in matches if m.isdigit())
            if max_pct <= rule["threshold"]:
                continue

        # 조항 참조 찾기
        art_refs = []
        for art in articles:
            art_text = art.get("raw_text", "") or str(art)
            for kw in found_keywords:
                if kw in art_text:
                    ref = f"제{art['number']}조({art['title']})"
                    if ref not in art_refs:
                        art_refs.append(ref)

        results.append({
            "keywords": found_keywords,
            "risk_level": rule["risk"],
            "article_ref": "、".join(art_refs) if art_refs else "계약서 내",
            "issue": rule["message"],
            "legal_basis": rule["article"],
        })

    return results


def determine_overall_risk(screening_results: list[dict]) -> str:
    levels = [r["risk_level"] for r in screening_results]
    if "HIGH" in levels:
        return "HIGH"
    if "MEDIUM" in levels:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────────────────────────────────────
# LLM 기반 스크리닝 (API 키가 있을 때)
# ─────────────────────────────────────────────────────────────────────────────
def llm_screening(
    articles: list[dict],
    retrieved_clauses: list,
    api_key: str,
) -> tuple[list[dict], str]:
    """OpenAI LLM으로 계약서를 분석합니다."""
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

        articles_text = "\n".join(
            f"제{a['number']}조({a['title']}): {a.get('raw_text','')[:300]}"
            for a in articles[:6]
        )
        clauses_text = "\n".join(
            f"- [{r.source}]: {r.text[:200]}"
            for r in retrieved_clauses[:5]
        ) if retrieved_clauses else "검색된 법령 없음"

        prompt = f"""당신은 법무 전문가입니다. 아래 계약서 조항을 분석하여 위험한 조항을 찾아주세요.

## 계약서 조항
{articles_text}

## 관련 법령·규정
{clauses_text}

각 위험 조항에 대해 반드시 아래 형식으로만 답하세요:
[조항참조] | [위험도: HIGH/MEDIUM/LOW] | [문제설명] | [근거법령]

위험 조항이 없으면 "위험 조항 없음"이라고만 답하세요."""

        response = llm.invoke(prompt)
        output = response.content.strip()

        results = []
        if "위험 조항 없음" in output:
            return [], "LOW"

        for line in output.splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            risk_raw = parts[1].upper()
            risk_level = "HIGH" if "HIGH" in risk_raw else ("MEDIUM" if "MEDIUM" in risk_raw else "LOW")
            results.append({
                "article_ref": parts[0],
                "risk_level": risk_level,
                "issue": parts[2],
                "legal_basis": parts[3],
                "keywords": [],
            })

        overall = determine_overall_risk(results)
        return results, overall

    except Exception as e:
        err_msg = str(e).lower()
        is_openai_error = any(word in err_msg for word in ["quota", "429", "rate_limit", "insufficient_quota", "apikey", "unauthorized", "api_key", "connection"])
        
        if is_openai_error:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5")
            print(f"\n{YELLOW}⚠ OpenAI API 호출 실패 ({e}). Ollama 모델로 자동 전환하여 시도합니다... (모델: {ollama_model}, 주소: {ollama_base_url}){RESET}")
            try:
                from langchain_openai import ChatOpenAI
                ollama_llm = ChatOpenAI(
                    model=ollama_model,
                    base_url=ollama_base_url,
                    api_key="ollama",
                    temperature=0
                )
                response = ollama_llm.invoke(prompt)
                output = response.content.strip()

                results = []
                if "위험 조항 없음" in output:
                    return [], "LOW"

                for line in output.splitlines():
                    line = line.strip()
                    if "|" not in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) < 4:
                        continue
                    risk_raw = parts[1].upper()
                    risk_level = "HIGH" if "HIGH" in risk_raw else ("MEDIUM" if "MEDIUM" in risk_raw else "LOW")
                    results.append({
                        "article_ref": parts[0],
                        "risk_level": risk_level,
                        "issue": parts[2],
                        "legal_basis": parts[3],
                        "keywords": [],
                    })

                overall = determine_overall_risk(results)
                print(f"{GREEN}✓ Ollama 모델 분석 성공{RESET}")
                return results, overall
            except Exception as ollama_err:
                print(f"{YELLOW}⚠ Ollama 모델 호출도 실패했습니다 ({ollama_err}). 키워드 기반 분석으로 전환합니다.{RESET}\n")
                return None, None
        else:
            print(f"\n{YELLOW}⚠ LLM 분석 실패 ({e}), 키워드 기반 분석으로 전환합니다.{RESET}\n")
            return None, None



# ─────────────────────────────────────────────────────────────────────────────
# 보고서 출력
# ─────────────────────────────────────────────────────────────────────────────
def format_report(
    file_path: str,
    articles: list[dict],
    screening_results: list[dict],
    overall_risk: str,
    mask_mapping: dict,
    elapsed: float,
    mode: str,
) -> str:
    lines = []
    sep = "═" * 60

    lines.append(sep)
    lines.append("  계약서 위험도 분석 보고서")
    lines.append(sep)
    lines.append(f"  대상 파일    : {Path(file_path).name}")
    lines.append(f"  분석 모드    : {mode}")
    lines.append(f"  감지된 조항수: {len(articles)}개 조(Article)")
    lines.append(f"  처리 시간    : {elapsed:.1f}초")
    lines.append(f"  종합 위험도  : {overall_risk}")
    lines.append(sep)

    if not screening_results:
        lines.append("\n[OK] 위험 조항이 감지되지 않았습니다.\n")
    else:
        lines.append(f"\n[!] 감지된 위험 조항: 총 {len(screening_results)}건\n")
        for i, r in enumerate(screening_results, 1):
            risk_icon = "[HIGH]" if r["risk_level"] == "HIGH" else ("[MED]" if r["risk_level"] == "MEDIUM" else "[LOW]")
            lines.append(f"  [{i}] {risk_icon} {r['risk_level']} — {r['article_ref']}")
            lines.append(f"      내용: {r['issue']}")
            lines.append(f"      근거: {r['legal_basis']}")
            if r.get("keywords"):
                lines.append(f"      감지어: {', '.join(r['keywords'])}")
            lines.append("")

    lines.append(sep)
    lines.append("  마스킹된 개인정보·기업정보")
    lines.append(sep)
    if mask_mapping:
        for token, original in mask_mapping.items():
            lines.append(f"  {token:20s} → {original}")
    else:
        lines.append("  (마스킹된 항목 없음)")

    lines.append(sep)
    lines.append("  권고사항")
    lines.append(sep)
    highs = [r for r in screening_results if r["risk_level"] == "HIGH"]
    meds  = [r for r in screening_results if r["risk_level"] == "MEDIUM"]
    if highs:
        lines.append("  [필수] 법무팀 검토 필수 -- HIGH 위험 조항이 감지되었습니다.")
        lines.append("         계약 체결 전 반드시 법무팀과 협의하세요.")
    elif meds:
        lines.append("  [권고] 법무팀 검토 권고 -- MEDIUM 위험 조항이 감지되었습니다.")
    else:
        lines.append("  [OK]  큰 위험 없음 -- 일반적인 수준의 검토 후 체결 가능합니다.")
    lines.append(sep)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="계약서 PDF/DOCX를 분석하여 위험도를 판단합니다."
    )
    parser.add_argument("--file", "-f", required=True, help="분석할 계약서 파일 경로 (PDF 또는 DOCX)")
    parser.add_argument("--api-key", help="OpenAI API 키 (미입력 시 키워드 기반 분석)")
    parser.add_argument("--db", default="tests/fixtures/sample_legal_db.json",
                        help="법령 DB JSON 파일 경로 (기본값: tests/fixtures/sample_legal_db.json)")
    parser.add_argument("--output", "-o", help="보고서를 저장할 파일 경로 (미입력 시 화면 출력)")
    args = parser.parse_args()

    print_banner()
    start = time.perf_counter()
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")

    # ── Step 1: 파일 파싱 ─────────────────────────────────────────────────────
    print_step(1, 4, "계약서 파싱 중")
    try:
        from modules.parser import parse_contract_file
        parsed = parse_contract_file(args.file)
        articles = parsed.articles
        full_text = parsed.raw_text
        print(f"   → {len(articles)}개 조(Article) 추출 완료")
    except Exception as e:
        print(f"{RED}파싱 실패: {e}{RESET}")
        sys.exit(1)

    # ── Step 2: 마스킹 ────────────────────────────────────────────────────────
    print_step(2, 4, "민감 정보 마스킹 중")
    try:
        from modules.masking import mask_text
        mask_result = mask_text(full_text)
        masked_text = mask_result.masked_text
        mask_mapping = mask_result.mapping
        print(f"   → {len(mask_mapping)}개 항목 마스킹 완료")
    except Exception as e:
        print(f"{YELLOW}마스킹 실패(건너뜀): {e}{RESET}")
        masked_text = full_text
        mask_mapping = {}

    # ── Step 3: 법령 검색 ─────────────────────────────────────────────────────
    print_step(3, 4, "관련 법령·규정 검색 중")
    retrieved_clauses = []
    try:
        if Path(args.db).exists():
            import json, numpy as np
            from modules.rag_retriever import HybridRetriever, LegalDocument

            with open(args.db, "r", encoding="utf-8") as f:
                db_data = json.load(f)
            documents = [LegalDocument(**d) for d in db_data]

            def simple_embed(text: str) -> np.ndarray:
                """API 키 없을 때 사용하는 단순 해시 기반 임베딩."""
                seed = abs(hash(text)) % (2**31)
                return np.random.default_rng(seed).random(384).astype(np.float32)

            if api_key:
                try:
                    from langchain_openai import OpenAIEmbeddings
                    embed_model = OpenAIEmbeddings(
                        model="text-embedding-3-small", dimensions=384, api_key=api_key
                    )
                    embed_fn = embed_model.embed_query
                    print("   → OpenAI 임베딩 사용")
                except Exception:
                    embed_fn = simple_embed
                    print("   → 단순 임베딩 사용 (폴백)")
            else:
                embed_fn = simple_embed
                print("   → 단순 임베딩 사용 (API 키 없음)")

            retriever = HybridRetriever(documents=documents, embed_fn=embed_fn)
            query = masked_text[:400]
            retrieved_clauses = retriever.retrieve(query, top_k=5)
            print(f"   → 관련 조항 {len(retrieved_clauses)}건 검색 완료")
        else:
            print(f"   → DB 파일 없음 ({args.db}), 법령 검색 건너뜀")
    except Exception as e:
        print(f"{YELLOW}법령 검색 실패(건너뜀): {e}{RESET}")

    # ── Step 4: 위험도 분석 ───────────────────────────────────────────────────
    print_step(4, 4, f"위험도 분석 중 ({'AI 분석' if api_key else '키워드 분석'})")
    mode = "AI (GPT-4o-mini)" if api_key else "키워드 기반"
    screening_results = []
    overall_risk = "LOW"

    if api_key:
        llm_results, llm_overall = llm_screening(articles, retrieved_clauses, api_key)
        if llm_results is not None:
            screening_results = llm_results
            overall_risk = llm_overall
        else:
            # LLM 실패 시 키워드 폴백
            screening_results = keyword_screening(full_text, articles)
            overall_risk = determine_overall_risk(screening_results)
            mode = "키워드 기반 (AI 폴백)"
    else:
        screening_results = keyword_screening(full_text, articles)
        overall_risk = determine_overall_risk(screening_results)

    print(f"   → 위험 조항 {len(screening_results)}건 감지")

    # ── 결과 출력 ─────────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - start
    report = format_report(
        file_path=args.file,
        articles=articles,
        screening_results=screening_results,
        overall_risk=overall_risk,
        mask_mapping=mask_mapping,
        elapsed=elapsed,
        mode=mode,
    )

    print()

    # 컬러 출력 (터미널)
    for line in report.splitlines():
        if "[HIGH]" in line or "HIGH" in line and "[" in line:
            print(f"{RED}{line}{RESET}")
        elif "[MED]" in line or "MEDIUM" in line and "[" in line:
            print(f"{YELLOW}{line}{RESET}")
        elif "[OK]" in line or "[LOW]" in line:
            print(f"{GREEN}{line}{RESET}")
        elif "[필수]" in line:
            print(f"{RED}{BOLD}{line}{RESET}")
        elif "[권고]" in line:
            print(f"{YELLOW}{line}{RESET}")
        elif line.startswith("="):
            print(f"{CYAN}{line}{RESET}")
        else:
            print(line)

    # 파일 저장
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\n{GREEN}보고서 저장 완료: {args.output}{RESET}")


if __name__ == "__main__":
    main()
