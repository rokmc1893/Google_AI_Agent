from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    source: str = "contract"
    filename: str = ""


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def chunk_document(
    text: str,
    *,
    chunk_size: int = 800,
    overlap: int = 120,
    source: str = "contract",
    filename: str = "",
    min_chunk_size: int = 80,
) -> list[TextChunk]:
    """
    한국어 계약서 안전 청킹 (문단 우선, 500~1000자 목표).
    """
    normalized = _normalize(text)
    if not normalized:
        return []

    paragraphs = re.split(r"\n{2,}|\n(?=\d+[\.\)]\s)|\n(?=제\d+)", normalized)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    merged: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(buf) + len(para) + 1 <= chunk_size:
            buf = f"{buf}\n{para}".strip() if buf else para
        else:
            if buf:
                merged.append(buf)
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    piece = para[i : i + chunk_size]
                    if len(piece) >= min_chunk_size:
                        merged.append(piece)
                buf = ""
            else:
                buf = para
    if buf:
        merged.append(buf)

    chunks: list[TextChunk] = []
    for idx, body in enumerate(merged):
        if len(body) < min_chunk_size and idx > 0:
            chunks[-1] = TextChunk(
                text=chunks[-1].text + "\n" + body,
                chunk_index=chunks[-1].chunk_index,
                source=source,
                filename=filename,
            )
            continue
        chunks.append(
            TextChunk(
                text=body,
                chunk_index=idx,
                source=source,
                filename=filename,
            )
        )

    return chunks
