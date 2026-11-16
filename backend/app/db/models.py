import enum
import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Dimensão fixa da coluna de vetores. Trocar exige migration + reprocessar documentos.
# 768 = gemini-embedding-001 reduzido (bom equilíbrio entre qualidade, espaço e velocidade).
EMBEDDING_DIM = 768


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class DocumentStatus(enum.StrEnum):
    UPLOADED = "uploaded"  # arquivo salvo, aguardando processamento
    PROCESSING = "processing"  # extração em andamento
    PROCESSED = "processed"  # texto extraído e salvo por página
    FAILED = "failed"  # erro registrado em Document.error


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    documents: Mapped[list["Document"]] = relationship(back_populates="collection")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("collection_id", "sha256", name="uq_document_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("collections.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))  # pdf | docx | txt | md
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(512))

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus, name="document_status", values_callable=lambda e: [m.value for m in e]
        ),
        default=DocumentStatus.UPLOADED,
    )
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    collection: Mapped[Collection | None] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chunk.chunk_index",
    )
    pages: Mapped[list["DocumentPage"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPage.page_number",
    )


class DocumentPage(Base):
    """Texto extraído por página — preserva a referência de origem para o RAG (Etapa 3+)."""

    __tablename__ = "document_pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_page"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page_number: Mapped[int] = mapped_column(Integer)  # começa em 1
    text: Mapped[str] = mapped_column(Text)

    document: Mapped[Document] = relationship(back_populates="pages")


class Chunk(Base):
    """Trecho do documento + seu embedding. É a unidade recuperada pelo RAG."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk"),
        # Índice HNSW para busca aproximada por similaridade de cosseno (Etapa 4).
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)  # ordem dentro do documento, a partir de 0
    text: Mapped[str] = mapped_column(Text)

    # Metadados de origem — permitem citar "arquivo.pdf, p. 3–4".
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)
    token_estimate: Mapped[int] = mapped_column(Integer)

    # Qual modelo gerou o vetor: vetores de modelos diferentes não são comparáveis.
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    document: Mapped[Document] = relationship(back_populates="chunks")
