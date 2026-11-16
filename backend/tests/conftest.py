import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.api import documents as documents_api
from app.core.config import Settings, get_settings
from app.db.models import EMBEDDING_DIM, Base
from app.db.session import get_db
from app.main import app
from app.providers.fake import FakeEmbeddingProvider, FakeLLMProvider
from app.providers.registry import get_embedding_provider, get_llm_provider
from app.storage.base import get_storage
from app.storage.local import LocalStorage

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://cognita:cognita@localhost:5432/cognita_test"
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    try:
        with eng.connect() as conn:
            conn.execute(text("create extension if not exists vector"))
            conn.commit()
    except OperationalError:
        pytest.skip("Banco de teste indisponível — rode `docker compose up -d`.")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine) -> Iterator[sessionmaker[Session]]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    with engine.begin() as conn:  # limpa os dados entre testes
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client(session_factory, tmp_path, monkeypatch) -> Iterator[TestClient]:
    storage = LocalStorage(tmp_path / "uploads")

    def _db() -> Iterator[Session]:
        with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_storage] = lambda: storage
    monkeypatch.setattr(documents_api, "get_sessionmaker", lambda: session_factory)
    embedder = FakeEmbeddingProvider(dimensions=EMBEDDING_DIM)
    monkeypatch.setattr(documents_api, "get_embedding_provider", lambda: embedder)
    app.dependency_overrides[get_embedding_provider] = lambda: embedder
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()
    # Configuração padrão (ignora o .env da máquina): testes não dependem de chaves reais.
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
