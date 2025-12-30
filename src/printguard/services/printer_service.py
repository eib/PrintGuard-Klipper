"""Consolidated printer service - manages printer instances, commands, inference, and defects."""

import logging
from typing import Optional, Dict
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.database import AsyncSession, async_session
from ..core.db_models import Printer, Component, PrinterComponentLink, Connection
from ..core.models import PrinterConfig, ComponentConfig, FeedSettings
from ..core.model import get_model
from ..core.inference import predict
from .streams import stream_manager
from .component_resolver import resolve_component
from .notifications import notify_defect
from .events import event_service
from ..providers import get_provider
from ..providers.base import StatusSource, CameraSource, ControlSink

logger = logging.getLogger(__name__)


class PrinterInstance(BaseModel):
    """Runtime state of a printer."""
    config: PrinterConfig
    status: Optional[StatusSource] = None
    camera: Optional[CameraSource] = None
    control: Optional[ControlSink] = None
    available_commands: list[str] = []

    model_config = {"arbitrary_types_allowed": True}


# Lightweight cache - invalidate on update
_instances: Dict[str, PrinterInstance] = {}


def invalidate_cache(printer_id: str) -> None:
    """Remove printer from cache (call after updates)."""
    _instances.pop(printer_id, None)


async def get_instance(printer_id: str, db: AsyncSession) -> Optional[PrinterInstance]:
    """Get printer instance, fetching from DB if not cached."""
    if printer_id in _instances:
        return _instances[printer_id]

    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    db_printer = result.scalar_one_or_none()
    if not db_printer:
        return None

    links_res = await db.execute(
        select(PrinterComponentLink)
        .where(PrinterComponentLink.printer_id == printer_id)
        .options(
            selectinload(PrinterComponentLink.component)
        )
        .execution_options(populate_existing=True)
    )
    links = list(links_res.scalars().all())
    comp_map = {link.role: link.component for link in links if link.component is not None}
    config = PrinterConfig(
        id=db_printer.id,
        name=db_printer.name,
        components={role: ComponentConfig(id=c.id, provider=c.provider, config=c.config) for role, c in comp_map.items()},
        client_public_key=db_printer.client_public_key,
        inference_sensitivity=db_printer.inference_sensitivity,
        inference_majority_voting=db_printer.inference_majority_voting,
        inference_target_fps=db_printer.inference_target_fps,
        detection_action=db_printer.detection_action,
        inference_paused=db_printer.inference_paused,
        auto_detection=getattr(db_printer, "auto_detection", False)
    )

    instance = PrinterInstance(config=config)

    # Resolve non-control components
    for role, db_comp in comp_map.items():
        if not role.startswith("control:"):
            setattr(instance, role, await resolve_component(db_comp, db))

    # Merge control: components into single provider
    control_components = {k: v for k, v in comp_map.items() if k.startswith("control:")}
    if control_components:
        merged_config = {}
        connection_id = None
        available_commands = []
        fallback_entity_id: str | None = None

        for role, component in control_components.items():
            action = role.split(":")[1]
            available_commands.append(action)
            if entity_id := component.entity_config.get("entity_id"):
                merged_config[f"{action}_entity_id"] = entity_id
                fallback_entity_id = fallback_entity_id or entity_id
            if not connection_id and component.connection_id:
                connection_id = component.connection_id

        if connection_id:
            conn_res = await db.execute(select(Connection).where(Connection.id == connection_id))
            if conn := conn_res.scalar_one_or_none():
                merged_config.update(conn.config)

        first_comp = next(iter(control_components.values()))
        if prov_cls := get_provider(first_comp.provider):
            if "entity_id" not in merged_config and fallback_entity_id:
                merged_config["entity_id"] = fallback_entity_id
            instance.control = prov_cls(**merged_config)
            instance.available_commands = available_commands

    elif "control" in comp_map:
        instance.control = await resolve_component(comp_map["control"], db)
        instance.available_commands = ["start", "pause", "resume", "stop"]

    _instances[printer_id] = instance
    return instance


async def set_inference_state(printer_id: str, running: bool, db: Optional[AsyncSession] = None) -> None:
    """Set inference running state - updates DB, cache, and active processor."""
    paused = not running

    async def _update(session: AsyncSession):
        result = await session.execute(select(Printer).where(Printer.id == printer_id))
        if db_printer := result.scalar_one_or_none():
            db_printer.inference_paused = paused
            await session.commit()

        if instance := await get_instance(printer_id, session):
            instance.config.inference_paused = paused

        if source := stream_manager.get_source(printer_id):
            if source.processor:
                source.processor.pause_inference = paused

        # Broadcast state change
        await event_service.broadcast(printer_id, "inference_state", {"running": running})
        logger.info(f"Inference {'stopped' if paused else 'started'} for printer {printer_id}")

    if db:
        await _update(db)
    else:
        async with async_session() as session:
            await _update(session)


async def execute_command(printer_id: str, command: str, db: Optional[AsyncSession] = None) -> dict:
    """Execute printer command (start/pause/resume/stop)."""
    async def _execute(session: AsyncSession) -> dict:
        instance = await get_instance(printer_id, session)
        if not instance:
            raise ValueError(f"Printer {printer_id} not found")
        if not instance.control:
            raise ValueError(f"Printer {printer_id} has no control")
        if command not in instance.available_commands:
            raise ValueError(f"Command {command} not available")

        await getattr(instance.control, command)()
        return {"status": "ok", "command": command}

    if db:
        return await _execute(db)
    async with async_session() as session:
        return await _execute(session)


async def handle_defect(
    printer_id: str,
    session_id: str,
    class_name: str,
    confidence: float,
    screenshot_path: Optional[str] = None,
    detection_action: str = "none"
) -> None:
    """Handle detected defect - execute action, stop inference, notify."""
    # Execute printer action if configured
    if detection_action and detection_action != "none":
        try:
            await execute_command(printer_id, detection_action)
        except Exception as e:
            logger.error(f"Defect action {detection_action} failed for {printer_id}: {e}")

    # Stop inference
    await set_inference_state(printer_id, running=False)

    # Broadcast defect event
    await event_service.broadcast(printer_id, "defect", {
        "class_name": class_name,
        "confidence": confidence,
        "screenshot": screenshot_path
    })

    # Send push notification
    notify_defect(session_id, class_name, confidence, screenshot_path)

    logger.info(f"Defect handled for {printer_id}: {class_name} ({confidence:.0%})")


def sync_settings(printer_id: str, sensitivity: float, majority_voting: int, target_fps: float, detection_action: str) -> None:
    """Sync printer settings to active stream processor."""
    source = stream_manager.get_source(printer_id)
    if not source:
        return

    source.settings.sensitivity = sensitivity
    source.settings.majority_voting = majority_voting
    source.settings.target_fps = target_fps
    source.settings.detection_action = detection_action
    source.processor.settings = source.settings
    logger.debug(f"Settings synced for {printer_id}")


async def start_stream(printer_id: str, db: Optional[AsyncSession] = None) -> bool:
    """Start camera stream and inference for printer. Returns True if started."""
    from .webrtc import start_track_processing

    async def _start(session: AsyncSession) -> bool:
        # Check if already streaming
        if stream_manager.get_source(printer_id):
            await set_inference_state(printer_id, running=True, db=session)
            return True

        instance = await get_instance(printer_id, session)
        if not instance or not instance.camera:
            logger.warning(f"Cannot start stream for {printer_id}: no camera")
            return False

        track, pc = await instance.camera.get_camera_track()
        if not track:
            logger.warning(f"Cannot start stream for {printer_id}: no track available")
            return False

        settings = FeedSettings(
            sensitivity=instance.config.inference_sensitivity,
            majority_voting=instance.config.inference_majority_voting,
            target_fps=instance.config.inference_target_fps,
            detection_action=instance.config.detection_action,
            inference_paused=False
        )

        model_info = get_model()
        processor = await start_track_processing(track, predict, model_info, settings, printer_id)
        processor.printer_id = printer_id

        async def on_defect(class_name: str, confidence: float, screenshot_path: str = None):
            await handle_defect(printer_id, printer_id, class_name, confidence, screenshot_path, settings.detection_action)

        processor.on_defect = on_defect

        if processor.relayed_track:
            await stream_manager.register_source(
                printer_id,
                processor.relayed_track,
                processor,
                pc=pc,
                device_name=f"{instance.config.name} Camera",
                settings=settings,
                printer_id=printer_id
            )

        await set_inference_state(printer_id, running=True, db=session)
        logger.info(f"Stream started for {printer_id}")
        return True

    if db:
        return await _start(db)
    async with async_session() as session:
        return await _start(session)


async def stop_stream(printer_id: str) -> None:
    """Stop inference (keeps stream alive for viewers)."""
    await set_inference_state(printer_id, running=False)
    logger.info(f"Inference stopped for {printer_id}")

