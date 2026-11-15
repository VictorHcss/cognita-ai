import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select

from app.api.deps import DbDep, SettingsDep, StorageDep
from app.api.schemas import DocumentOut, PageOut
from app.db.models import Document, DocumentPage, DocumentStatus
from app.db.session import get_sessionmaker
from app.services import documents as service
from app.storage.base import FileStorage

router = APIRouter(prefix="/documents", tags=["documentos"])


def _process_in_background(storage: FileStorage, document_id: uuid.UUID) -> None:
    # Roda depois da resposta HTTP: precisa de uma sessão própria.
    with get_sessionmaker()() as db:
        service.process_document(db, storage, document_id)


def _get_or_404(db: DbDep, document_id: uuid.UUID) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "Documento não encontrado.")
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: DbDep,
    collection_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if collection_id:
        query = query.where(Document.collection_id == collection_id)
    return list(db.scalars(query))


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    db: DbDep,
    storage: StorageDep,
    settings: SettingsDep,
    background: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    collection_id: Annotated[uuid.UUID | None, Form()] = None,
) -> Document:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    try:
        doc = service.create_document(
            db,
            storage,
            filename=file.filename or "sem-nome",
            data=data,
            collection_id=collection_id,
            max_bytes=max_bytes,
        )
    except service.DocumentError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    background.add_task(_process_in_background, storage, doc.id)
    return doc


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: DbDep) -> Document:
    return _get_or_404(db, document_id)


@router.get("/{document_id}/pages", response_model=list[PageOut])
def get_pages(document_id: uuid.UUID, db: DbDep) -> list[DocumentPage]:
    return _get_or_404(db, document_id).pages


@router.post("/{document_id}/reprocess", response_model=DocumentOut)
def reprocess_document(
    document_id: uuid.UUID, db: DbDep, storage: StorageDep, background: BackgroundTasks
) -> Document:
    doc = _get_or_404(db, document_id)
    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(409, "O documento já está em processamento.")
    doc.status = DocumentStatus.UPLOADED
    db.commit()
    background.add_task(_process_in_background, storage, doc.id)
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: DbDep, storage: StorageDep) -> None:
    try:
        service.delete_document(db, storage, document_id)
    except service.DocumentError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
