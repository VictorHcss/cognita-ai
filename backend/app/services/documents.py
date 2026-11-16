"""Regras de negócio da biblioteca documental: upload, processamento, exclusão."""

import asyncio
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    EMBEDDING_DIM,
    Chunk,
    Collection,
    Document,
    DocumentPage,
    DocumentStatus,
)
from app.processing.chunking import chunk_pages
from app.processing.cleaning import clean_text
from app.processing.extractors import ExtractionError, extract, file_type_from_name
from app.providers.base import EmbeddingProvider, ProviderError
from app.storage.base import FileStorage, StorageError

logger = logging.getLogger("cognita.documents")

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain; charset=utf-8",
    "md": "text/markdown; charset=utf-8",
}


class DocumentError(Exception):
    """Erro de regra de negócio, com o status HTTP sugerido."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def create_document(
    db: Session,
    storage: FileStorage,
    *,
    filename: str,
    data: bytes,
    collection_id: uuid.UUID | None,
    max_bytes: int,
) -> Document:
    file_type = file_type_from_name(filename)
    if file_type is None:
        raise DocumentError("Formato não suportado. Use PDF, DOCX, TXT ou Markdown.", 415)
    if not data:
        raise DocumentError("Arquivo vazio.")
    if len(data) > max_bytes:
        raise DocumentError(f"Arquivo excede o limite de {max_bytes // (1024 * 1024)} MB.", 413)
    if collection_id and db.get(Collection, collection_id) is None:
        raise DocumentError("Coleção não encontrada.", 404)

    sha256 = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(
        select(Document).where(Document.sha256 == sha256, Document.collection_id == collection_id)
    )
    if duplicate:
        raise DocumentError(f"Este arquivo já existe nesta coleção ({duplicate.filename}).", 409)

    doc_id = uuid.uuid4()
    storage_key = f"{doc_id}/original.{file_type}"
    try:
        storage.save(storage_key, data, CONTENT_TYPES[file_type])
    except StorageError as exc:
        raise DocumentError(f"Falha ao armazenar o arquivo: {exc}", 502) from exc

    doc = Document(
        id=doc_id,
        collection_id=collection_id,
        filename=filename,
        file_type=file_type,
        size_bytes=len(data),
        sha256=sha256,
        storage_key=storage_key,
        status=DocumentStatus.UPLOADED,
    )
    db.add(doc)
    db.commit()
    logger.info("document_uploaded", extra={"data": {"id": str(doc_id), "size": len(data)}})
    return doc


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 1000
    overlap: int = 150


def mark_failed(db: Session, doc: Document, message: str) -> Document:
    doc.status = DocumentStatus.FAILED
    doc.error = message
    db.commit()
    logger.warning("document_failed", extra={"data": {"id": str(doc.id), "error": message}})
    return doc


def process_document(
    db: Session,
    storage: FileStorage,
    embedder: EmbeddingProvider,
    document_id: uuid.UUID,
    chunking: ChunkingConfig = ChunkingConfig(),
) -> Document:
    """Pipeline de ingestão: extrair → limpar → salvar páginas → chunking → embeddings.

    Idempotente: reprocessar substitui páginas e chunks.
    """
    doc = db.get(Document, document_id)
    if doc is None:
        raise DocumentError("Documento não encontrado.", 404)

    doc.status = DocumentStatus.PROCESSING
    doc.error = None
    db.commit()
    timings: dict[str, float] = {}

    # 1. Extração e limpeza
    t0 = time.perf_counter()
    try:
        raw_pages = extract(doc.file_type, storage.read(doc.storage_key))
    except (ExtractionError, StorageError) as exc:
        return mark_failed(db, doc, str(exc))
    pages = [(p.page_number, clean_text(p.text)) for p in raw_pages]
    timings["extract_ms"] = (time.perf_counter() - t0) * 1000

    db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    db.execute(delete(DocumentPage).where(DocumentPage.document_id == doc.id))
    db.add_all(DocumentPage(document_id=doc.id, page_number=n, text=t) for n, t in pages)
    doc.page_count = len(pages)
    doc.char_count = sum(len(t) for _, t in pages)
    doc.chunk_count = 0
    db.commit()

    if doc.char_count == 0:
        return mark_failed(
            db, doc, "Nenhum texto extraído (o PDF pode ser escaneado; OCR ainda não é suportado)."
        )

    # 2. Chunking
    t0 = time.perf_counter()
    pieces = chunk_pages(pages, chunking.chunk_size, chunking.overlap)
    timings["chunk_ms"] = (time.perf_counter() - t0) * 1000

    # 3. Embeddings
    if embedder.dimensions != EMBEDDING_DIM:
        return mark_failed(
            db,
            doc,
            f"O provedor gera vetores de {embedder.dimensions} dimensões, mas o banco espera "
            f"{EMBEDDING_DIM}. Ajuste EMBEDDING_DIMENSIONS.",
        )
    t0 = time.perf_counter()
    try:
        vectors = asyncio.run(embedder.embed([c.text for c in pieces], task="document"))
    except ProviderError as exc:
        return mark_failed(db, doc, f"Falha ao gerar embeddings: {exc}")
    timings["embed_ms"] = (time.perf_counter() - t0) * 1000

    model = f"{embedder.name}/{embedder.model}"
    db.add_all(
        Chunk(
            document_id=doc.id,
            chunk_index=c.index,
            text=c.text,
            page_start=c.page_start,
            page_end=c.page_end,
            char_start=c.char_start,
            char_end=c.char_end,
            token_estimate=c.token_estimate,
            embedding_model=model,
            embedding=vector,
        )
        for c, vector in zip(pieces, vectors, strict=True)
    )
    doc.chunk_count = len(pieces)
    doc.status = DocumentStatus.PROCESSED
    db.commit()
    db.refresh(doc)

    logger.info(
        "document_processed",
        extra={
            "data": {
                "id": str(doc.id),
                "pages": doc.page_count,
                "chars": doc.char_count,
                "chunks": doc.chunk_count,
                "embedding_model": model,
                **{k: round(v, 1) for k, v in timings.items()},
            }
        },
    )
    return doc


def delete_document(db: Session, storage: FileStorage, document_id: uuid.UUID) -> None:
    doc = db.get(Document, document_id)
    if doc is None:
        raise DocumentError("Documento não encontrado.", 404)
    try:
        storage.delete(doc.storage_key)
    except StorageError as exc:
        # O registro é removido mesmo assim; o arquivo órfão fica registrado no log.
        logger.warning(
            "storage_delete_failed", extra={"data": {"key": doc.storage_key, "error": str(exc)}}
        )
    db.delete(doc)
    db.commit()
