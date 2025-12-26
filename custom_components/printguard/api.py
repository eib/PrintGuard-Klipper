"""API client for PrintGuard."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any
import uuid

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CAMERA,
    CONF_CLIENT_ID,
    CONF_CLIENT_PRIVATE_KEY,
    CONF_CLIENT_PUBLIC_KEY,
    CONF_CLIENT_SECRET,
    CONF_PAUSE_ENTITY,
    CONF_PRINTER_NAME,
    CONF_RESUME_ENTITY,
    CONF_SERVER_PUBLIC_KEY,
    CONF_START_ENTITY,
    CONF_STOP_ENTITY,
)
from .crypto import CryptoHandler

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidPrinterConfig(HomeAssistantError):
    """Error to indicate there is an invalid printer configuration."""


class PrinterAlreadyExists(HomeAssistantError):
    """Error to indicate the printer already exists."""


class PrintGuardApiClient:
    """API client for PrintGuard server communication."""

    def __init__(
        self,
        hass: HomeAssistant,
        url: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        server_pub_key: str | None = None,
        client_priv_key: str | None = None,
        client_pub_key: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._hass = hass
        self._url = url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._server_pub_key = server_pub_key
        self._client_priv_key = client_priv_key
        self._client_pub_key = client_pub_key
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """Get an access token using M2M credentials."""
        if self._access_token:
            return self._access_token
        if not self._client_id or not self._client_secret:
            raise CannotConnect("Missing Client ID or Client Secret")
        session = async_get_clientsession(self._hass)
        data = {
            "grant_type": "password",
            "username": self._client_id,
            "password": self._client_secret,
            "scope": "admin printer:read printer:write rtc:stream"
        }
        async with session.post(f"{self._url}/api/auth/token", data=data, timeout=10) as resp:
            if resp.status != 200:
                detail = await resp.text()
                _LOGGER.error("Failed to get access token: %s", detail)
                raise CannotConnect(f"Authentication failed: {resp.status}")
            payload = await resp.json()
            self._access_token = payload["access_token"]
            return self._access_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        params: dict | None = None,
        is_retry: bool = False,
    ) -> aiohttp.ClientResponse:
        """Make an optionally encrypted request."""
        session = async_get_clientsession(self._hass)
        headers: dict[str, str] = {}
        try:
            token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"
        except CannotConnect:
            if not endpoint.startswith("/api/crypto/key"):
                raise
        request_data = data
        if self._encryption_enabled:
            headers["X-Encrypted"] = "true"
            headers["X-Client-Public-Key"] = self._client_pub_key
            if data is not None:
                handler = self._get_crypto_handler()
                shared_key = handler.derive_shared_key(base64.b64decode(self._server_pub_key))
                request_data = handler.encrypt(json.dumps(data).encode("utf-8"), shared_key)
                headers["Content-Type"] = "application/octet-stream"
        resp = await session.request(
            method, f"{self._url}{endpoint}", data=request_data, params=params, headers=headers, timeout=10
        )
        if resp.status == 401 and not is_retry:
            self._access_token = None
            return await self._request(method, endpoint, data, params, is_retry=True)  
        return resp

    async def fetch_server_public_key(self) -> str:
        """Fetch the server public key (unencrypted endpoint)."""
        session = async_get_clientsession(self._hass)
        async with session.get(f"{self._url}/api/crypto/key", timeout=10) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            key = payload.get("public_key")
            if not key:
                raise CannotConnect("Missing 'public_key' in server response")
            return key

    async def refresh_server_public_key(self) -> str:
        """Refresh the cached server public key and return it."""
        new_key = await self.fetch_server_public_key()
        self._server_pub_key = new_key
        return new_key

    async def _decrypt_response(self, response: aiohttp.ClientResponse) -> Any:
        """Decrypt and parse JSON response."""
        if response.headers.get("X-Encrypted") == "true" and self._encryption_enabled:
            handler = self._get_crypto_handler()
            shared_key = handler.derive_shared_key(base64.b64decode(self._server_pub_key))
            encrypted_data = await response.read()
            return json.loads(handler.decrypt(encrypted_data, shared_key).decode("utf-8"))
        return await response.json()

    async def _read_error_detail(self, response: aiohttp.ClientResponse) -> str:
        """Read error details from the server (decrypt if needed)."""
        try:
            payload = await self._decrypt_response(response)
            if isinstance(payload, dict):
                detail = payload.get("detail", payload)
                return json.dumps(detail, ensure_ascii=False)
            return str(payload)
        except Exception:
            try:
                raw = await response.read()
                return raw.decode("utf-8", errors="replace")
            except Exception:
                return "<unable to read error body>"

    async def get_printers(self) -> list[dict]:
        """Fetch all printers."""
        resp = await self._request("GET", "/api/printer/")
        if resp.status == 200:
            printers = await self._decrypt_response(resp)
            return printers
        return []

    async def get_printer(self, printer_id: str) -> dict | None:
        """Fetch a single printer."""
        resp = await self._request("GET", f"/api/printer/{printer_id}")
        return await self._decrypt_response(resp) if resp.status == 200 else None

    async def send_printer_command(self, printer_id: str, command: str) -> bool:
        """Send a command to a printer."""
        resp = await self._request("POST", f"/api/printer/{printer_id}/{command}")
        return resp.status == 200

    async def get_connections(self) -> list[dict]:
        """Fetch all connections."""
        resp = await self._request("GET", "/api/connections")
        if resp.status == 200:
            return await self._decrypt_response(resp)
        return []

    async def create_connection(self, name: str, provider: str, config: dict) -> dict:
        """Create a new connection."""
        data = {"name": name, "provider": provider, "config": config}
        resp = await self._request("POST", "/api/connections", data=data)
        if resp.status == 200:
            return await self._decrypt_response(resp)
        detail = await self._read_error_detail(resp)
        raise CannotConnect(detail)

    async def create_component(
        self,
        name: str,
        type: str,
        provider: str,
        connection_id: str | None,
        entity_config: dict,
    ) -> dict:
        """Create a new component."""
        data = {
            "name": name,
            "type": type,
            "provider": provider,
            "connection_id": connection_id,
            "entity_config": entity_config,
        }
        resp = await self._request("POST", "/api/components", data=data)
        if resp.status == 200:
            return await self._decrypt_response(resp)
        detail = await self._read_error_detail(resp)
        raise InvalidPrinterConfig(detail)

    async def delete_component(self, component_id: str) -> bool:
        """Delete a component."""
        resp = await self._request("DELETE", f"/api/components/{component_id}")
        return resp.status in (200, 204)

    async def get_prediction_result(self, session_id: str) -> dict | None:
        """Fetch prediction result."""
        resp = await self._request("GET", f"/api/rtc/result/{session_id}")
        return await self._decrypt_response(resp) if resp.status == 200 else None

    async def get_snapshot(self, session_id: str) -> bytes | None:
        """Fetch snapshot image."""
        try:
            resp = await self._request("GET", f"/api/rtc/snapshot/{session_id}")
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.debug("PrintGuard get_snapshot failed: session_id=%s err=%s", session_id, err)
            return None
        if resp.status == 200:
            if resp.headers.get("X-Encrypted") == "true" and self._encryption_enabled:
                handler = self._get_crypto_handler()
                shared_key = handler.derive_shared_key(base64.b64decode(self._server_pub_key))
                return handler.decrypt(await resp.read(), shared_key)
            return await resp.read()
        return None

    async def send_webrtc_offer(self, session_id: str, offer_sdp: str) -> str | None:
        """Send WebRTC offer."""
        try:
            resp = await self._request(
                "POST",
                f"/api/rtc/view/{session_id}",
                data={"sdp": offer_sdp, "type": "offer"},
            )
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.debug("PrintGuard send_webrtc_offer failed: session_id=%s err=%s", session_id, err)
            return None
        if resp.status == 200:
            answer = await self._decrypt_response(resp)
            return answer.get("sdp")
        return None

    async def start_printer_stream(self, printer_id: str, session_id: str | None = None) -> str | None:
        """Ask the server to create/link a stream session for a printer.

        The server sets `linked_session_id` and registers a WebRTC session that
        snapshots and viewer connections can attach to.
        """
        session_id = session_id or uuid.uuid4().hex
        try:
            resp = await self._request(
                "POST",
                f"/api/printer/{printer_id}/stream",
                params={"session_id": session_id},
            )
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.debug(
                "PrintGuard start_printer_stream failed: printer_id=%s session_id=%s err=%s",
                printer_id,
                session_id,
                err,
            )
            return None
        if resp.status == 200:
            payload = await self._decrypt_response(resp)
            if isinstance(payload, dict) and payload.get("status") == "success":
                return payload.get("session_id") or session_id
        detail = await self._read_error_detail(resp)
        _LOGGER.debug(
            "PrintGuard start_printer_stream failed: printer_id=%s status=%s detail=%s",
            printer_id,
            resp.status,
            detail,
        )
        return None

    async def delete_printer(self, printer_id: str) -> bool:
        """Delete a printer."""
        resp = await self._request("DELETE", f"/api/printer/{printer_id}")
        return resp.status in (200, 204, 404)
