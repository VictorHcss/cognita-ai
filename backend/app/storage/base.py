"""Armazenamento dos arquivos originais, atrás de uma interface (como os provedores de IA)."""

from functools import lru_cache
from typing import Protocol

from app.core.config import Settings, get_settings


class StorageError(RuntimeError):
    pass


class FileStorage(Protocol):
    name: str

    def save(self, key: str, data: bytes, content_type: str) -> None: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


def build_storage(settings: Settings) -> FileStorage:
    if settings.storage_backend == "supabase":
        from app.storage.supabase import SupabaseStorage

        return SupabaseStorage(
            settings.supabase_url,
            settings.supabase_service_key.get_secret_value(),
            settings.supabase_bucket,
        )
    from app.storage.local import LocalStorage

    return LocalStorage(settings.local_storage_dir)


@lru_cache
def get_storage() -> FileStorage:
    """Dependência do FastAPI."""
    return build_storage(get_settings())
