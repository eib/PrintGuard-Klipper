"""Config flow for PrintGuard integration."""
from __future__ import annotations

import base64
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    CannotConnect,
    InvalidPrinterConfig,
    PrinterAlreadyExists,
    PrintGuardApiClient,
)
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_PRIVATE_KEY,
    CONF_CLIENT_PUBLIC_KEY,
    CONF_CLIENT_SECRET,
    CONF_CONNECTION_ID,
    CONF_ERROR_STATES,
    CONF_PAUSED_STATES,
    CONF_PRINTING_STATES,
    CONF_SERVER_PUBLIC_KEY,
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
)
from .crypto import CryptoHandler

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="http://localhost:8000"): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_TOKEN): str,
    }
)


async def _fetch_server_public_key(hass: HomeAssistant, url: str) -> str:
    """Fetch server public key from the PrintGuard server."""
    session = async_get_clientsession(hass)
    async with session.get(f"{url}/api/crypto/key", timeout=10) as response:
        response.raise_for_status()
        payload = await response.json()
        public_key = payload.get("public_key")
        if not public_key:
            raise HomeAssistantError("Missing 'public_key' in server response")
        return public_key


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    url = data[CONF_URL].rstrip("/")
    try:
        session = async_get_clientsession(hass)
        async with session.get(f"{url}/api/health", timeout=10) as response:
            response.raise_for_status()
        await _fetch_server_public_key(hass, url)
    except Exception as err:
        raise CannotConnect(str(err)) from err
    return {"title": "PrintGuard"}


def _build_api_client(hass: HomeAssistant, data: dict[str, Any]) -> PrintGuardApiClient:
    """Build an API client from entry/config-flow data."""
    url = data[CONF_URL].rstrip("/")
    return PrintGuardApiClient(
        hass,
        url,
        data.get(CONF_CLIENT_ID),
        data.get(CONF_CLIENT_SECRET),
        data.get(CONF_SERVER_PUBLIC_KEY),
        data.get(CONF_CLIENT_PRIVATE_KEY),
        data.get(CONF_CLIENT_PUBLIC_KEY),
    )

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PrintGuard."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._base_data: dict[str, Any] = {}
        self._cameras: list[str] = []
        self._sensors: list[str] = []
        self._controls: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                url = user_input[CONF_URL].rstrip("/")
                user_input[CONF_SERVER_PUBLIC_KEY] = await _fetch_server_public_key(
                    self.hass, url
                )
                handler = CryptoHandler()
                user_input[CONF_CLIENT_PRIVATE_KEY] = base64.b64encode(
                    handler.get_private_key_bytes()
                ).decode("utf-8")
                user_input[CONF_CLIENT_PUBLIC_KEY] = handler.get_public_key_b64()
                await validate_input(self.hass, user_input)
                
                api_client = _build_api_client(self.hass, user_input)
                await api_client._get_access_token()
                
                # Register HA as a connection
                hass_url = self.hass.config.internal_url or self.hass.config.external_url or "http://localhost:8123"
                connection = await api_client.create_connection(
                    name="Home Assistant",
                    provider="homeassistant",
                    config={
                        "hass_url": hass_url,
                        "token": user_input[CONF_TOKEN]
                    }
                )
                user_input[CONF_CONNECTION_ID] = connection["id"]
                
                self._base_data = user_input
                return await self.async_step_cameras()
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle selecting cameras to export."""
        if user_input is not None:
            self._cameras = user_input["cameras"]
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="cameras",
            data_schema=vol.Schema({
                vol.Required("cameras"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="camera", multiple=True)
                )
            })
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle selecting status sensors to export."""
        if user_input is not None:
            self._sensors = user_input["sensors"]
            return await self.async_step_status_mapping()

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Required("sensors"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "binary_sensor"], multiple=True)
                )
            })
        )

    async def async_step_status_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle defining status mapping for sensors."""
        if user_input is not None:
            self._base_data.update(user_input)
            return await self.async_step_controls()

        return self.async_show_form(
            step_id="status_mapping",
            data_schema=vol.Schema({
                vol.Required(CONF_PRINTING_STATES, default="printing,on,active"): str,
                vol.Required(CONF_PAUSED_STATES, default="paused"): str,
                vol.Required(CONF_ERROR_STATES, default="error,unavailable,unknown"): str,
            })
        )

    async def async_step_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle selecting control entities to export."""
        if user_input is not None:
            self._controls = user_input["controls"]
            await self._export_components()
            return self.async_create_entry(title="PrintGuard", data=self._base_data)

        return self.async_show_form(
            step_id="controls",
            data_schema=vol.Schema({
                vol.Required("controls"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "button"], multiple=True)
                )
            })
        )

    async def _export_components(self) -> None:
        """Export all selected entities to PrintGuard API."""
        api_client = _build_api_client(self.hass, self._base_data)
        conn_id = self._base_data[CONF_CONNECTION_ID]
        
        # Export Cameras
        for entity_id in self._cameras:
            state = self.hass.states.get(entity_id)
            name = state.name if state else entity_id
            await api_client.create_component(
                name=name,
                type="camera",
                provider="homeassistant",
                connection_id=conn_id,
                entity_config={"entity_id": entity_id}
            )
            
        # Export Status Sensors
        for entity_id in self._sensors:
            state = self.hass.states.get(entity_id)
            name = state.name if state else entity_id
            await api_client.create_component(
                name=name,
                type="status",
                provider="homeassistant",
                connection_id=conn_id,
                entity_config={
                    "entity_id": entity_id,
                    CONF_PRINTING_STATES: self._base_data[CONF_PRINTING_STATES],
                    CONF_PAUSED_STATES: self._base_data[CONF_PAUSED_STATES],
                    CONF_ERROR_STATES: self._base_data[CONF_ERROR_STATES],
                }
            )
            
        # Export Controls
        for entity_id in self._controls:
            state = self.hass.states.get(entity_id)
            name = state.name if state else entity_id
            await api_client.create_component(
                name=name,
                type="control",
                provider="homeassistant",
                connection_id=conn_id,
            entity_config={"entity_id": entity_id}
        )

