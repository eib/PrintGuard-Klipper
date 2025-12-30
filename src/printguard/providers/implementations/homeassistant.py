"""Home Assistant printer provider implementation."""

from typing import Optional, Tuple
import logging
import asyncio
import httpx

from aiortc import RTCPeerConnection, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer

from ..base import PrinterProvider
from ..registry import register
from ...services.component_validator import get_component_type_from_entity, is_camera_entity, is_status_entity

logger = logging.getLogger(__name__)


async def _retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    timeout_exceptions: tuple = (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException)
):
    """
    Retry a function with exponential backoff for timeout exceptions.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 10.0)
        backoff_factor: Factor to multiply delay by after each retry (default: 2.0)
        timeout_exceptions: Tuple of exception types to retry on (default: httpx timeout exceptions)
    
    Returns:
        Result of the function call
        
    Raises:
        Last exception if all retries are exhausted
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except timeout_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Timeout exception (attempt {attempt + 1}/{max_retries + 1}): {type(e).__name__}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed with timeout exception: {type(e).__name__}")
        except Exception as e:
            raise
    if last_exception:
        raise last_exception

@register("homeassistant")
class HomeAssistantProvider(PrinterProvider):
    """Provider for Home Assistant API."""

    def __init__(self, hass_url: str, token: str, entity_id: str, 
                 start_entity_id: Optional[str] = None,
                 pause_entity_id: Optional[str] = None,
                 resume_entity_id: Optional[str] = None,
                 stop_entity_id: Optional[str] = None,
                 printing_state: Optional[str] = None,
                 paused_state: Optional[str] = None,
                 error_state: Optional[str] = None,
                 state_attribute: Optional[str] = None):
        self.hass_url = hass_url.rstrip("/")
        self.token = token
        self.entity_id = entity_id
        self.start_entity_id = start_entity_id
        self.pause_entity_id = pause_entity_id
        self.resume_entity_id = resume_entity_id
        self.stop_entity_id = stop_entity_id
        self.printing_state = (printing_state or "printing").strip().lower()
        self.paused_state = (paused_state or "paused").strip().lower()
        self.error_state = (error_state or "error").strip().lower()
        self.state_attribute = state_attribute
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.client: Optional[httpx.AsyncClient] = None
        self._player: Optional[MediaPlayer] = None

    @property
    def name(self) -> str:
        return "homeassistant"

    @classmethod
    def get_schema(cls) -> dict:
        return {
            "connection_fields": [
                {"name": "hass_url", "type": "string", "required": True, "label": "HA URL"},
                {"name": "token", "type": "password", "required": True, "label": "Access Token"}
            ],
            "entity_fields": [
                {"name": "entity_id", "type": "string", "required": True, "label": "Entity ID"},
                {"name": "printing_state", "type": "combobox", "required": True, "label": "Printing State", "default": "printing", "condition": "type == 'status'"},
                {"name": "paused_state", "type": "combobox", "required": True, "label": "Paused State", "default": "paused", "condition": "type == 'status'"},
                {"name": "error_state", "type": "combobox", "required": True, "label": "Error State", "default": "error", "condition": "type == 'status'"}
            ]
        }

    @classmethod
    async def validate_connection(cls, config: dict) -> bool:
        """Test connection to HA."""
        hass_url = config.get("hass_url", "").rstrip("/")
        token = config.get("token", "")
        if not hass_url or not token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                async def _validate():
                    resp = await client.get(
                        f"{hass_url}/api/",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    return resp
                resp = await _retry_with_backoff(_validate, max_retries=2)
                return resp.status_code == 200 and "message" in resp.json() and resp.json()["message"] == "API running."
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"HA validation failed after retries: {e}")
            return False
        except Exception as e:
            logger.error(f"HA validation failed: {e}")
            return False

    @classmethod
    async def validate_component(cls, config: dict) -> bool:
        """Test if HA entity exists and required fields are present."""
        hass_url = config.get("hass_url", "").rstrip("/")
        token = config.get("token", "")
        entity_id = config.get("entity_id", "")
        
        if not all([hass_url, token, entity_id]):
            return False

        if is_status_entity(entity_id):
            if not all([config.get("printing_state"), config.get("paused_state"), config.get("error_state")]):
                return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                async def _validate_component():
                    resp = await client.get(
                        f"{hass_url}/api/states/{entity_id}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    return resp
                resp = await _retry_with_backoff(_validate_component, max_retries=2)
                return resp.status_code == 200
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"HA component validation failed for {entity_id} after retries: {e}")
            return False
        except Exception as e:
            logger.error(f"HA component validation failed for {entity_id}: {e}")
            return False

    @classmethod
    async def list_entities(cls, config: dict) -> list[dict]:
        """Fetch available camera and status entities from HA."""
        hass_url = config.get("hass_url", "").rstrip("/")
        token = config.get("token", "")
        if not hass_url or not token:
            return []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async def _list_entities():
                    resp = await client.get(
                        f"{hass_url}/api/states",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    resp.raise_for_status()
                    return resp.json()
                states = await _retry_with_backoff(_list_entities, max_retries=2, initial_delay=2.0)
                entities = []
                for state in states:
                    entity_id = state["entity_id"]
                    attributes = state.get("attributes", {})
                    name = attributes.get("friendly_name", entity_id)
                    comp_type = get_component_type_from_entity(entity_id)

                    if comp_type:
                        if comp_type == "status":
                            options = attributes.get("options")
                            if not isinstance(options, list) or not options:
                                continue

                        entities.append({"id": entity_id, "name": name, "type": comp_type})
                return entities
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"HA entity listing failed for {hass_url} after retries: {e}")
            return []
        except Exception as e:
            logger.error(f"HA entity listing failed for {hass_url}: {e}")
            return []

    @classmethod
    async def get_entity_details(cls, config: dict, entity_id: str) -> dict:
        """Fetch full state and attributes for a specific entity from HA."""
        hass_url = config.get("hass_url", "").rstrip("/")
        token = config.get("token", "")
        if not all([hass_url, token, entity_id]):
            return {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                async def _get_details():
                    resp = await client.get(
                        f"{hass_url}/api/states/{entity_id}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    resp.raise_for_status()
                    return resp.json()
                return await _retry_with_backoff(_get_details, max_retries=2)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"HA entity detail fetch failed for {entity_id} at {hass_url} after retries: {e}")
            return {}
        except Exception as e:
            logger.error(f"HA entity detail fetch failed for {entity_id} at {hass_url}: {e}")
            return {}

    async def _call_service(self, domain: str, service: str, service_data: dict) -> None:
        """Call a Home Assistant service."""
        if not self.client:
            await self.connect()
        
        async def _make_service_call():
            """Inner function to make service call for retry logic."""
            response = await self.client.post(
                f"/api/services/{domain}/{service}",
                json=service_data
            )
            response.raise_for_status()
            return response
        
        try:
            await _retry_with_backoff(_make_service_call)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"Failed to call HA service {domain}.{service} after retries: {e}")
        except Exception as e:
            logger.error(f"Failed to call HA service {domain}.{service}: {e}")

    async def _call_action(self, entity_id: Optional[str]) -> None:
        """Helper to call the appropriate service for an entity."""
        if not entity_id:
            return
        domain = entity_id.split(".")[0]
        service = "press" if domain == "button" else "turn_on"
        if "stop" in entity_id or "cancel" in entity_id:
            if domain == "switch":
                service = "turn_off"
        await self._call_service(domain, service, {"entity_id": entity_id})

    async def connect(self) -> None:
        """Initialize the HTTP client and test connection."""
        if not self.client:
            self.client = httpx.AsyncClient(
                base_url=self.hass_url, 
                headers=self.headers,
                timeout=20.0
            )
        logger.info(f"Testing connection to HA at {self.hass_url} for entity {self.entity_id}")
        
        async def _test_connection():
            """Inner function to test connection for retry logic."""
            response = await self.client.get(f"/api/states/{self.entity_id}")
            response.raise_for_status()
            return response
        
        try:
            response = await _retry_with_backoff(_test_connection)
            logger.info(f"Successfully connected to HA, entity {self.entity_id} state: {response.json().get('state')}")
            # Test camera snapshot proxy access (single JPEG)
            if is_camera_entity(self.entity_id):
                proxy_url = f"/api/camera_proxy/{self.entity_id}"
                logger.debug(f"Testing camera proxy access: {proxy_url}")
                
                async def _test_camera():
                    """Inner function to test camera access for retry logic."""
                    test_resp = await self.client.get(proxy_url, timeout=10.0)
                    return test_resp
                
                try:
                    test_resp = await _retry_with_backoff(_test_camera, max_retries=2)
                    if test_resp.status_code == 200:
                        content_type = test_resp.headers.get("Content-Type", "unknown")
                        logger.info(f"Camera proxy access verified. Content-Type: {content_type}")
                    else:
                        logger.warning(f"Camera proxy access failed with status {test_resp.status_code}: {test_resp.text[:100]}")
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
                    logger.warning(f"Camera proxy access timeout (non-critical): {e}")
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"HA connection test failed after retries: {e}")
            raise
        except Exception as e:
            logger.error(f"HA connection test failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the HTTP client and any active media players."""
        if self._player:
            if hasattr(self._player, "stop"):
                self._player.stop()
            self._player = None
        if self.client:
            await self.client.aclose()
            self.client = None

    async def is_printing(self) -> bool:
        """Check if the printer is currently printing."""
        return await self.get_status() == "printing"

    async def get_status(self) -> str:
        """Get the current status of the printer."""
        if not self.client:
            await self.connect()
        
        async def _fetch_status():
            """Inner function to fetch status for retry logic."""
            response = await self.client.get(f"/api/states/{self.entity_id}")
            response.raise_for_status()
            return response.json()
        
        try:
            data = await _retry_with_backoff(_fetch_status)
            
            if is_status_entity(self.entity_id):
                state = str(data.get("state", "")).lower()
            elif self.state_attribute:
                state = str(data.get("attributes", {}).get(self.state_attribute, "")).lower()
            else:
                state = str(data.get("state", "")).lower()
            
            if state == self.error_state:
                return "error"
            if state == self.printing_state:
                return "printing"
            if state == self.paused_state:
                return "paused"
            return "idle"
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"Failed to get status for {self.entity_id} after retries: {e}")
            return "error"
        except Exception as e:
            logger.error(f"Failed to get status for {self.entity_id}: {e}")
            return "error"

    async def start(self) -> None:
        """Start/resume the print job."""
        await self._call_action(self.start_entity_id)

    async def pause(self) -> None:
        """Pause the current print."""
        await self._call_action(self.pause_entity_id)

    async def resume(self) -> None:
        """Resume the current print."""
        await self._call_action(self.resume_entity_id or self.start_entity_id)

    async def stop(self) -> None:
        """Cancel the current job."""
        await self._call_action(self.stop_entity_id)

    async def get_camera_track(self) -> Tuple[Optional[MediaStreamTrack], Optional[RTCPeerConnection]]:
        """Return a video track from Home Assistant's camera proxy."""
        if not self.client:
            await self.connect()
        if not is_camera_entity(self.entity_id):
            logger.warning(f"Entity {self.entity_id} is not a camera")
            return None, None
        stream_url = f"{self.hass_url}/api/camera_proxy_stream/{self.entity_id}"
        logger.info(f"Attempting to get camera track from {stream_url}")
        for fmt in ["mjpeg", None]:
            try:
                headers = f"Authorization: Bearer {self.token}"
                options = {
                    "headers": headers,
                    "fflags": "nobuffer",
                    "flags": "low_delay",
                    "probesize": "32",
                    "analyzeduration": "0",
                }
                if self.hass_url.startswith("https"):
                    options["tls_verify"] = "0"
                    options["verify_hostname"] = "0"
                logger.debug(f"Trying MediaPlayer with format={fmt} for {self.entity_id}")
                player = MediaPlayer(stream_url, format=fmt, options=options)
                if player.video:
                    try:
                        logger.debug(f"Verifying stream for {self.entity_id} (format={fmt})...")
                        await asyncio.wait_for(player.video.recv(), timeout=10.0)
                        logger.info(f"Successfully verified stream for {self.entity_id} with format={fmt}")
                        self._player = player
                        return self._player.video, None
                    except Exception as e:
                        logger.warning(f"Format {fmt} failed verification: {type(e).__name__} {e}")
                        if hasattr(player, "stop"): player.stop()
                        continue
            except Exception as e:
                logger.warning(f"Failed to create MediaPlayer with format {fmt}: {e}")
                continue
        logger.error(f"All stream formats failed for {self.entity_id}")
        return None, None
