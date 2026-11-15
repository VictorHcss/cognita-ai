"""Supabase Storage via API REST (sem SDK, para manter dependências enxutas).

Requer um bucket privado (padrão: "documents") e a service role key — que só existe no backend.
"""

import httpx

from app.storage.base import StorageError


class SupabaseStorage:
    name = "supabase"

    def __init__(self, url: str, service_key: str, bucket: str, timeout: float = 60.0) -> None:
        if not url or not service_key:
            raise StorageError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios.")
        self.bucket = bucket
        self._client = httpx.Client(
            base_url=f"{url.rstrip('/')}/storage/v1",
            headers={"Authorization": f"Bearer {service_key}", "apikey": service_key},
            timeout=timeout,
        )

    def _check(self, response: httpx.Response, action: str) -> None:
        if response.is_error:
            raise StorageError(f"Supabase ({action}) {response.status_code}: {response.text}")

    def save(self, key: str, data: bytes, content_type: str) -> None:
        r = self._client.post(
            f"/object/{self.bucket}/{key}",
            content=data,
            headers={"Content-Type": content_type, "x-upsert": "true"},
        )
        self._check(r, "upload")

    def read(self, key: str) -> bytes:
        r = self._client.get(f"/object/{self.bucket}/{key}")
        self._check(r, "download")
        return r.content

    def delete(self, key: str) -> None:
        r = self._client.request("DELETE", f"/object/{self.bucket}", json={"prefixes": [key]})
        self._check(r, "delete")
