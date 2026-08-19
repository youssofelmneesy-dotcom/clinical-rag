from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

from backend.config import ChunkingConfig, SourceDocument
from backend.models import Chunk


HEADING_PATTERNS = {
    "gold-2026": (
        re.compile(r"^(CHAPTER\s+\d+[:.\s].+)$", re.IGNORECASE),
        re.compile(r"^([A-Z][A-Z0-9 ,:;()/\-\u2013]{8,})$"),
        re.compile(r"^(\d+(?:\.\d+)*\s+[A-Z][A-Za-z0-9 ,:;()/\-\u2013]{8,})$"),
    ),
    "nice-ng115": (
        re.compile(r"^(\d+(?:\.\d+)+\s+[A-Z].+)$"),
        re.compile(r"^(Recommendations|Rationale and impact|Context|Terms used in this guideline)$", re.IGNORECASE),
        re.compile(r"^([A-Z][A-Za-z ,:;()/\-\u2013]{10,})$"),
    ),
}

RECOMMENDATION_PATTERN = re.compile(r"^\d+(?:\.\d+){2,}\s+")
BULLET_PATTERN = re.compile(r"^([*•\-]|\([a-z]\)|[a-z]\))\s+")


@dataclass(frozen=True)
class LogicalUnit:
    text: str
    page_start: int
    page_end: int
    section: str
    subsection: str | None


def chunk_pages(
    pages: list[dict],
    source: SourceDocument,
    config: ChunkingConfig | None = None,
) -> list[Chunk]:
    config = config or ChunkingConfig()
    units = list(_logical_units(pages, source.document_id))
    chunk_groups = _group_units(units, config)
    chunks: list[Chunk] = []
    for index, group in enumerate(chunk_groups):
        if group[0].section.upper() == "REFERENCES":
            continue
        text = "\n\n".join(unit.text for unit in group).strip()
        if _skip_chunk(text):
            continue
        if len(text) < config.min_chunk_size and chunks:
            previous = chunks.pop()
            text = f"{previous.text}\n\n{text}".strip()
            page_start = min(previous.page_start or previous.page, group[0].page_start)
            page_end = max(previous.page_end or previous.page, group[-1].page_end)
            section = previous.section if previous.section != "Unknown" else group[0].section
            subsection = previous.subsection or group[0].subsection
            index -= 1
        else:
            page_start = group[0].page_start
            page_end = group[-1].page_end
            section = group[0].section
            subsection = group[0].subsection
        chunk_id = _chunk_id(source.document_id, page_start, page_end, index, text)
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=source.document_id,
                document_name=source.document_name,
                source_filename=source.filename,
                page=page_start,
                section=section or "Unknown",
                subsection=subsection,
                page_start=page_start,
                page_end=page_end,
                source_type=source.source_type,
                publication_date=source.publication_date,
                update_date=source.update_date,
                jurisdiction=source.jurisdiction,
                text=text,
            )
        )
    return chunks


def detect_heading(line: str, document_id: str) -> str | None:
    candidate = _clean_line(line)
    if not candidate or len(candidate) > 140:
        return None
    if _looks_like_sentence(candidate):
        return None
    for pattern in HEADING_PATTERNS.get(document_id, ()):
        match = pattern.match(candidate)
        if match:
            return match.group(1).strip()
    return None


def _logical_units(pages: list[dict], document_id: str) -> Iterable[LogicalUnit]:
    section = "Unknown"
    subsection: str | None = None
    paragraph_lines: list[str] = []
    paragraph_start_page = 1

    for page in pages:
        page_number = int(page["page"])
        lines = [_clean_line(line) for line in str(page.get("text", "")).splitlines()]
        lines = [line for line in lines if line and not _skip_line(line)]
        for line in lines:
            heading = detect_heading(line, document_id)
            if heading:
                if paragraph_lines:
                    yield LogicalUnit(
                        text=_join_paragraph(paragraph_lines),
                        page_start=paragraph_start_page,
                        page_end=page_number,
                        section=section,
                        subsection=subsection,
                    )
                    paragraph_lines = []
                if _is_subsection(heading):
                    subsection = heading
                else:
                    section = heading
                    subsection = None
                yield LogicalUnit(
                    text=heading,
                    page_start=page_number,
                    page_end=page_number,
                    section=section,
                    subsection=subsection,
                )
                continue

            starts_new = (
                not paragraph_lines
                or RECOMMENDATION_PATTERN.match(line)
                or BULLET_PATTERN.match(line)
                or paragraph_lines[-1].endswith((".", ":", ";", "?"))
            )
            if starts_new and paragraph_lines:
                yield LogicalUnit(
                    text=_join_paragraph(paragraph_lines),
                    page_start=paragraph_start_page,
                    page_end=page_number,
                    section=section,
                    subsection=subsection,
                )
                paragraph_lines = []
            if not paragraph_lines:
                paragraph_start_page = page_number
            paragraph_lines.append(line)

    if paragraph_lines:
        yield LogicalUnit(
            text=_join_paragraph(paragraph_lines),
            page_start=paragraph_start_page,
            page_end=paragraph_start_page,
            section=section,
            subsection=subsection,
        )


def _group_units(units: list[LogicalUnit], config: ChunkingConfig) -> list[list[LogicalUnit]]:
    groups: list[list[LogicalUnit]] = []
    current: list[LogicalUnit] = []
    current_len = 0
    for unit in units:
        unit_len = len(unit.text)
        boundary_change = current and (
            unit.section != current[-1].section or unit.page_start != current[-1].page_end
        )
        if current and current_len + unit_len > config.chunk_size and not _is_recommendation_continuation(unit):
            groups.append(current)
            current = _overlap_units(current, config.chunk_overlap)
            current_len = sum(len(item.text) for item in current)
        elif boundary_change and current_len >= config.min_chunk_size and current_len + unit_len > config.chunk_size:
            groups.append(current)
            current = []
            current_len = 0
        current.append(unit)
        current_len += unit_len
    if current:
        groups.append(current)
    return groups


def _overlap_units(units: list[LogicalUnit], overlap: int) -> list[LogicalUnit]:
    if overlap <= 0:
        return []
    selected: list[LogicalUnit] = []
    total = 0
    for unit in reversed(units):
        if RECOMMENDATION_PATTERN.match(unit.text):
            break
        selected.insert(0, unit)
        total += len(unit.text)
        if total >= overlap:
            break
    return selected


def _is_subsection(heading: str) -> bool:
    return bool(re.match(r"^\d+(?:\.\d+){2,}\s+", heading))


def _is_recommendation_continuation(unit: LogicalUnit) -> bool:
    return bool(RECOMMENDATION_PATTERN.match(unit.text) or BULLET_PATTERN.match(unit.text))


def _looks_like_sentence(text: str) -> bool:
    return text.endswith(".") and len(text.split()) > 6 and not text.isupper()


def _join_paragraph(lines: list[str]) -> str:
    text = " ".join(lines)
    return re.sub(r"\s+", " ", text).strip()


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _skip_line(line: str) -> bool:
    normalized = line.strip().lower()
    return (
        normalized == "copyright material - do not copy or distribute"
        or "important purpose & liability disclaimer" in normalized
    )


def _skip_chunk(text: str) -> bool:
    normalized = text.lower()
    reference_markers = len(re.findall(r"\bet al\.\b|\bdoi:|\bpmid:|\bjama\b|\blancet\b|\bthorax\b", normalized))
    return reference_markers >= 4 and "recommend" not in normalized


def _chunk_id(document_id: str, page_start: int, page_end: int, index: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}|{page_start}|{page_end}|{index}|{text}".encode("utf-8")).hexdigest()
    return f"{document_id}:{digest[:16]}"
