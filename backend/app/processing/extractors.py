"""Extração de texto por formato. Cada extrator devolve uma lista de páginas.

- PDF: uma entrada por página real (PyMuPDF).
- DOCX: o formato não guarda paginação; o documento inteiro vira a "página" 1.
- TXT / Markdown: página 1.
"""

import io
from dataclasses import dataclass

import docx
import pymupdf

SUPPORTED_TYPES = {"pdf", "docx", "txt", "md"}


class ExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int  # começa em 1
    text: str


def file_type_from_name(filename: str) -> str | None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext = "md" if ext == "markdown" else ext
    return ext if ext in SUPPORTED_TYPES else None


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def extract_pdf(data: bytes) -> list[ExtractedPage]:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ExtractionError("PDF protegido por senha.")
            return [
                ExtractedPage(i + 1, page.get_text("text", sort=True)) for i, page in enumerate(pdf)
            ]
    except ExtractionError:
        raise
    except Exception as exc:  # PyMuPDF lança tipos variados para arquivos corrompidos
        raise ExtractionError(f"PDF inválido: {exc}") from exc


def extract_docx(data: bytes) -> list[ExtractedPage]:
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError(f"DOCX inválido: {exc}") from exc
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    return [ExtractedPage(1, "\n".join(parts))]


def extract_plain(data: bytes) -> list[ExtractedPage]:
    return [ExtractedPage(1, _decode_text(data))]


def extract(file_type: str, data: bytes) -> list[ExtractedPage]:
    match file_type:
        case "pdf":
            return extract_pdf(data)
        case "docx":
            return extract_docx(data)
        case "txt" | "md":
            return extract_plain(data)
    raise ExtractionError(f"Formato não suportado: {file_type}")
