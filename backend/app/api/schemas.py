import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import DocumentStatus


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    document_count: int = 0


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    collection_id: uuid.UUID | None
    filename: str
    file_type: str
    size_bytes: int
    status: DocumentStatus
    error: str | None
    page_count: int
    char_count: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int
    text: str


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_index: int
    text: str
    page_start: int
    page_end: int
    char_start: int
    char_end: int
    token_estimate: int
    embedding_model: str
