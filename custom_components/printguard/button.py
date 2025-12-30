"""Support for PrintGuard button entities."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PrintGuardEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PrintGuard buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [PrintGuardRefreshButton(coordinator)]
    
    for p_id, p_data in coordinator.data.items():
        info = p_data["info"]
        components = info.get("components", {})

        control_actions = [k.split(":")[1] for k in components.keys() if k.startswith("control:")]
        
        if control_actions:
            for action in control_actions:
                entities.append(
                    PrintGuardControlButton(coordinator, p_id, info["name"], action)
                )
        elif info.get("has_control"):
            for command in ["start", "pause", "resume", "stop"]:
                entities.append(
                    PrintGuardControlButton(
                        coordinator, p_id, info["name"], command
                    )
                )
    
    async_add_entities(entities)


class PrintGuardRefreshButton(ButtonEntity):
    """Button to refresh PrintGuard data."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator) -> None:
        """Initialize."""
        self.coordinator = coordinator
        self._attr_name = "Refresh"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry.entry_id}_refresh"

    async def async_press(self) -> None:
        """Refresh data."""
        await self.coordinator.async_request_refresh()


class PrintGuardControlButton(PrintGuardEntity, ButtonEntity):
    """Button to control a PrintGuard printer."""

    def __init__(self, coordinator, p_id, p_name, command) -> None:
        """Initialize."""
        super().__init__(coordinator, p_id, p_name)
        self._command = command
        self._attr_name = command.capitalize()
        self._attr_unique_id = f"{DOMAIN}_{p_id}_{command}"
        self._attr_icon = {
            "start": "mdi:play",
            "pause": "mdi:pause",
            "resume": "mdi:play-pause",
            "stop": "mdi:stop",
        }.get(command)

    async def async_press(self) -> None:
        """Send command."""
        await self.coordinator.api_client.send_printer_command(
            self._printer_id, self._command
        )
        await self.coordinator.async_request_refresh()
