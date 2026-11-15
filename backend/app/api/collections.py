import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbDep
from app.api.schemas import CollectionCreate, CollectionOut
from app.db.models import Collection, Document

router = APIRouter(prefix="/collections", tags=["coleções"])


@router.get("", response_model=list[CollectionOut])
def list_collections(db: DbDep) -> list[CollectionOut]:
    rows = db.execute(
        select(Collection, func.count(Document.id))
        .outerjoin(Document)
        .group_by(Collection.id)
        .order_by(Collection.name)
    ).all()
    return [
        CollectionOut.model_validate(c).model_copy(update={"document_count": n}) for c, n in rows
    ]


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: DbDep) -> CollectionOut:
    collection = Collection(name=payload.name.strip(), description=payload.description.strip())
    db.add(collection)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe uma coleção com esse nome.") from exc
    return CollectionOut.model_validate(collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: uuid.UUID, db: DbDep) -> None:
    """Remove a coleção. Os documentos continuam na biblioteca, sem coleção."""
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(404, "Coleção não encontrada.")
    db.delete(collection)
    db.commit()
