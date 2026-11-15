from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.storage.base import FileStorage, get_storage

DbDep = Annotated[Session, Depends(get_db)]
StorageDep = Annotated[FileStorage, Depends(get_storage)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
