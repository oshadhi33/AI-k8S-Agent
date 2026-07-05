"""InsForge REST client for database, auth, and realtime."""

from __future__ import annotations

import httpx

from config import settings


class InsForgeClient:
    def __init__(self) -> None:
        self.base_url = settings.insforge_base_url.rstrip("/")
        self._anon_key = settings.insforge_anon_key
        self._service_key = settings.insforge_service_key

    def _headers(self, user_token: str | None = None, use_service: bool = False) -> dict:
        token = user_token or (self._service_key if use_service else self._anon_key)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_records(
        self,
        table: str,
        params: dict | None = None,
        user_token: str | None = None,
    ) -> tuple[list, int | None]:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(
                f"{self.base_url}/api/database/records/{table}",
                headers=self._headers(user_token),
                params=params or {},
            )
            resp.raise_for_status()
            raw_total = resp.headers.get("X-Total-Count")
            return resp.json(), int(raw_total) if raw_total else None

    async def create_records(
        self,
        table: str,
        records: list[dict],
        user_token: str | None = None,
    ) -> list:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                f"{self.base_url}/api/database/records/{table}",
                headers={**self._headers(user_token), "Prefer": "return=representation"},
                json=records,
            )
            resp.raise_for_status()
            return resp.json()

    async def update_records(
        self,
        table: str,
        filters: dict,
        data: dict,
        user_token: str | None = None,
    ) -> list:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.patch(
                f"{self.base_url}/api/database/records/{table}",
                headers={**self._headers(user_token), "Prefer": "return=representation"},
                params=filters,
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    async def publish_message(
        self,
        channel: str,
        payload: dict,
        user_token: str | None = None,
    ) -> dict:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                f"{self.base_url}/api/realtime/messages",
                headers=self._headers(user_token, use_service=True),
                json={"channel": channel, "payload": payload},
            )
            resp.raise_for_status()
            return resp.json()

    async def verify_session(self, access_token: str) -> dict | None:
        if not self.base_url:
            return None
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get(
                f"{self.base_url}/api/auth/sessions/current",
                headers=self._headers(access_token),
            )
            if resp.status_code == 401:
                return None
            resp.raise_for_status()
            return resp.json()


insforge = InsForgeClient()
