from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}
PREVIEW_LEN = 500


@dataclass
class ParsedDocument:
    text: str
    filename: str
    file_type: str


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _parse_txt(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("텍스트 파일 인코딩을 해석할 수 없습니다.")


def _parse_pdf(data: bytes) -> str:
    import fitz

    parts: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text().strip()
            if page_text:
                parts.append(page_text)
    if not parts:
        raise ValueError("PDF에서 추출할 텍스트가 없습니다.")
    return "\n\n".join(parts)


def _parse_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    parts: list[str] = []

    for para in document.paragraphs:
        t = para.text.strip()
        if t:
            parts.append(t)

    for table in document.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    if not parts:
        raise ValueError("Word 문서에서 추출할 텍스트가 없습니다.")
    return "\n".join(parts)


def parse_bytes(filename: str, data: bytes) -> ParsedDocument:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 형식입니다. 허용: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    if ext == ".txt":
        raw = _parse_txt(data)
    elif ext == ".pdf":
        raw = _parse_pdf(data)
    else:
        raw = _parse_docx(data)

    text = _normalize_text(raw)
    if not text:
        raise HTTPException(status_code=422, detail="문서에서 유효한 텍스트를 추출하지 못했습니다.")

    return ParsedDocument(text=text, filename=filename, file_type=ext.lstrip("."))


async def parse_upload(file: UploadFile, max_bytes: int) -> ParsedDocument:
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 필요합니다.")

    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기는 {max_bytes // (1024 * 1024)}MB 이하여야 합니다.",
        )
    if len(data) == 0:
        raise HTTPException(status_code=422, detail="빈 파일입니다.")

    try:
        return parse_bytes(file.filename, data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"문서 파싱 실패: {exc}") from exc
