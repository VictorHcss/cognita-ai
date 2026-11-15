from fastapi.testclient import TestClient

from tests.factories import make_pdf


def _upload(client: TestClient, name: str, data: bytes, collection_id: str | None = None):
    form = {"collection_id": collection_id} if collection_id else {}
    return client.post("/api/documents", files={"file": (name, data)}, data=form)


def test_collection_crud(client: TestClient) -> None:
    r = client.post("/api/collections", json={"name": "Livros", "description": "Leituras"})
    assert r.status_code == 201
    assert client.post("/api/collections", json={"name": "Livros"}).status_code == 409

    listed = client.get("/api/collections").json()
    assert [c["name"] for c in listed] == ["Livros"]

    assert client.delete(f"/api/collections/{r.json()['id']}").status_code == 204
    assert client.get("/api/collections").json() == []


def test_upload_pdf_is_processed_with_pages(client: TestClient) -> None:
    col = client.post("/api/collections", json={"name": "Apostilas"}).json()
    r = _upload(client, "aula.pdf", make_pdf(["Capitulo 1", "Capitulo 2"]), col["id"])
    assert r.status_code == 201
    doc_id = r.json()["id"]

    # TestClient executa as background tasks antes de devolver a resposta.
    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "processed"
    assert doc["page_count"] == 2

    pages = client.get(f"/api/documents/{doc_id}/pages").json()
    assert pages[1]["page_number"] == 2
    assert "Capitulo 2" in pages[1]["text"]

    in_collection = client.get("/api/documents", params={"collection_id": col["id"]}).json()
    assert [d["id"] for d in in_collection] == [doc_id]
    assert client.get("/api/collections").json()[0]["document_count"] == 1


def test_upload_rejects_unsupported_and_duplicates(client: TestClient) -> None:
    assert _upload(client, "virus.exe", b"MZ").status_code == 415
    assert _upload(client, "vazio.txt", b"").status_code == 400
    assert _upload(client, "notas.md", b"# Notas").status_code == 201
    assert _upload(client, "copia.md", b"# Notas").status_code == 409


def test_invalid_file_is_marked_failed_and_can_be_reprocessed(client: TestClient) -> None:
    doc_id = _upload(client, "quebrado.pdf", b"nao e pdf").json()["id"]
    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "PDF inválido" in doc["error"]

    again = client.post(f"/api/documents/{doc_id}/reprocess")
    assert again.status_code == 200
    assert client.get(f"/api/documents/{doc_id}").json()["status"] == "failed"


def test_delete_document_removes_stored_file(client: TestClient, tmp_path) -> None:
    doc_id = _upload(client, "a.txt", b"conteudo").json()["id"]
    uploads = tmp_path / "uploads"
    assert (uploads / doc_id).is_dir()

    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
    assert not (uploads / doc_id).exists()
    assert uploads.is_dir()
