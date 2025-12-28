"""Printer control endpoints."""

import logging
from typing import Any, Optional, Union
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Security, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...core.models import (
    PrinterConfig, PrinterInfo, PrinterStatus, FeedSettings,
    ComponentConfig, ComponentInfo, PrinterUpdate
)
from ...core.database import get_db, AsyncSession
from ...core.db_models import Printer, Component, PrinterComponentLink, PrinterNotificationSubscription
from ...core.model import get_model
from ...core.inference import predict
from ...providers import list_providers as get_available_providers, get_provider
from ...providers.base import StatusSource, CameraSource, ControlSink
from ...services.webrtc import start_track_processing
from ...services.streams import stream_manager
from ..crypto_utils import EncryptedRoute
from ..auth_utils import get_current_identity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/printer", tags=["printer"], route_class=EncryptedRoute)


class PrinterInstance(BaseModel):
    """Internal runtime state of a printer."""
    config: PrinterConfig
    status: Optional[StatusSource] = None
    camera: Optional[CameraSource] = None
    control: Optional[ControlSink] = None

    model_config = {"arbitrary_types_allowed": True}


_printers: dict[str, PrinterInstance] = {}


async def _resolve_component(comp: Component, db: AsyncSession) -> Any:
    """Instantiate a provider component from DB model."""
    provider = comp.provider
    config = {}
    if comp.connection_id:
        if not comp.connection:
            from ...core.db_models import Connection
            res = await db.execute(select(Connection).where(Connection.id == comp.connection_id))
            comp.connection = res.scalar_one_or_none()
            
        if comp.connection:
            config.update(comp.connection.config)
            
    config.update(comp.entity_config or {})

    prov_cls = get_provider(provider)
    if not prov_cls:
        logger.warning(f"Provider class not found for: {provider}")
        return None
    try:
        return prov_cls(**config)
    except Exception as e:
        logger.error(f"Failed to instantiate provider {provider} with config {config}: {e}")
        return None


async def _get_or_create_printer_instance(printer_id: str, db: AsyncSession) -> Optional[PrinterInstance]:
    """Get printer instance from cache or initialize from DB."""
    if printer_id in _printers:
        return _printers[printer_id]
    result = await db.execute(
        select(Printer).where(Printer.id == printer_id).options(
            selectinload(Printer.component_links)
            .joinedload(PrinterComponentLink.component)
            .selectinload(Component.connection)
        )
    )
    db_printer = result.scalar_one_or_none()
    if not db_printer:
        return None
    comp_map = {link.role: link.component for link in db_printer.component_links}
    config = PrinterConfig(
        id=db_printer.id,
        name=db_printer.name,
        components={role: ComponentConfig(id=c.id, provider=c.provider, config=c.config) for role, c in comp_map.items()},
        client_public_key=db_printer.client_public_key,
        inference_sensitivity=db_printer.inference_sensitivity,
        inference_majority_voting=db_printer.inference_majority_voting,
        inference_target_fps=db_printer.inference_target_fps,
        detection_action=db_printer.detection_action,
        inference_paused=db_printer.inference_paused
    )
    instance = PrinterInstance(config=config)
    for role, db_comp in comp_map.items():
        setattr(instance, role, await _resolve_component(db_comp, db))
    _printers[printer_id] = instance
    return instance


async def trigger_printer_action(printer_id: str, action: str):
    """Trigger an action on a printer."""
    if action == "none":
        return
        
    from ...core.database import async_session as SessionLocal
    async with SessionLocal() as db:
        instance = await _get_or_create_printer_instance(printer_id, db)
        if not instance or not instance.control:
            logger.warning(f"Cannot trigger action {action} for printer {printer_id}: instance or control not found")
            return
            
        try:
            if action == "pause":
                logger.info(f"Auto-pausing printer {printer_id} due to defect")
                await instance.control.pause()
            elif action == "stop":
                logger.info(f"Auto-stopping printer {printer_id} due to defect")
                await instance.control.stop()
        except Exception as e:
            logger.error(f"Failed to trigger auto action {action} for printer {printer_id}: {e}")


@router.get("/providers")
async def list_providers(_: any = Security(get_current_identity, scopes=["printer:read"])) -> list[str]:
    """List available printer providers."""
    return get_available_providers()


@router.get("/providers/{provider}/schema")
async def get_provider_schema(
    provider: str,
    _: any = Security(get_current_identity, scopes=["printer:read"])
) -> dict:
    """Return JSON schema for provider configuration fields."""
    prov_cls = get_provider(provider)
    if not prov_cls:
        raise HTTPException(status_code=404, detail="Provider schema not found")
    return prov_cls.get_schema()


@router.post("", response_model=PrinterInfo)
async def register_printer(
    config: PrinterConfig, 
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:write"])
) -> PrinterInfo:
    """Register a new modular printer."""
    db_printer = Printer(
        name=config.name,
        client_public_key=config.client_public_key,
        inference_sensitivity=config.inference_sensitivity,
        inference_majority_voting=config.inference_majority_voting,
        inference_target_fps=config.inference_target_fps,
        detection_action=config.detection_action
    )
    if config.id:
        db_printer.id = config.id
    db.add(db_printer)
    await db.flush()
    roles = ["status", "camera", "control"]
    for role in roles:
        comp_data = getattr(config.components, role)
        if not comp_data:
            continue
        db_comp = None
        if isinstance(comp_data, str):
            res = await db.execute(select(Component).where(Component.id == comp_data))
            db_comp = res.scalar_one_or_none()
            if not db_comp:
                raise HTTPException(status_code=400, detail=f"Component {comp_data} not found")
        elif isinstance(comp_data, ComponentConfig):
            if comp_data.id:
                res = await db.execute(select(Component).where(Component.id == comp_data.id))
                db_comp = res.scalar_one_or_none()
                if not db_comp:
                    raise HTTPException(status_code=400, detail=f"Component {comp_data.id} not found")
            else:
                db_comp = Component(
                    name=comp_data.name,
                    provider=comp_data.provider,
                    config=comp_data.config
                )
                db.add(db_comp)
                await db.flush()
        if db_comp:
            link = PrinterComponentLink(
                printer_id=db_printer.id,
                component_id=db_comp.id,
                role=role
            )
            db.add(link)
    await db.commit()
    return await get_printer(db_printer.id, db, user)


@router.put("/{printer_id}", response_model=PrinterInfo)
async def update_printer(
    printer_id: str,
    config: PrinterUpdate,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:write"])
) -> PrinterInfo:
    """Update printer components."""
    result = await db.execute(
        select(Printer)
        .where(Printer.id == printer_id)
        .options(selectinload(Printer.component_links))
    )
    db_printer = result.scalar_one_or_none()
    if not db_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if config.name is not None:
        db_printer.name = config.name
    
    if config.inference_sensitivity is not None:
        db_printer.inference_sensitivity = config.inference_sensitivity
    if config.inference_majority_voting is not None:
        db_printer.inference_majority_voting = config.inference_majority_voting
    if config.inference_target_fps is not None:
        db_printer.inference_target_fps = config.inference_target_fps
    if config.detection_action is not None:
        db_printer.detection_action = config.detection_action
        
    if config.components is not None:
        for link in db_printer.component_links:
            await db.delete(link)
        await db.flush()
        roles = ["status", "camera", "control"]
        for role in roles:
            comp_id = getattr(config.components, role)
            if not comp_id:
                continue
            res = await db.execute(select(Component).where(Component.id == comp_id))
            if not res.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"Component {comp_id} not found")
                
            link = PrinterComponentLink(
                printer_id=db_printer.id,
                component_id=comp_id,
                role=role
            )
            db.add(link)
            
    await db.commit()
    if printer_id in _printers:
        _printers.pop(printer_id)

    source = stream_manager.get_source(printer_id)
    if source:
        logger.info(f"Updating active stream for printer {printer_id} with target_fps {db_printer.inference_target_fps}")
        source.settings.sensitivity = db_printer.inference_sensitivity
        source.settings.majority_voting = db_printer.inference_majority_voting
        source.settings.target_fps = db_printer.inference_target_fps
        source.settings.detection_action = db_printer.detection_action
        source.processor.settings = source.settings

    return await get_printer(printer_id, db, user)


@router.get("", response_model=list[PrinterInfo])
async def list_printers(
    endpoint: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"])
) -> list[PrinterInfo]:
    """List all registered printers."""
    result = await db.execute(select(Printer.id))
    printer_ids = result.scalars().all()
    return [await get_printer(pid, db, user, endpoint) for pid in printer_ids]


@router.get("/{printer_id}", response_model=PrinterInfo)
async def get_printer(
    printer_id: str, 
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"]),
    endpoint: Optional[str] = Query(None)
) -> PrinterInfo:
    """Get printer status."""
    instance = await _get_or_create_printer_instance(printer_id, db)
    if not instance:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    status = PrinterStatus.DISCONNECTED
    if instance.status:
        try:
            is_printing = await instance.status.is_printing()
            status = PrinterStatus.PRINTING if is_printing else PrinterStatus.IDLE
        except Exception:
            status = PrinterStatus.ERROR
    elif instance.camera:
        status = PrinterStatus.IDLE
    result = await db.execute(
        select(PrinterComponentLink).where(PrinterComponentLink.printer_id == printer_id).options(
            selectinload(PrinterComponentLink.component)
        )
    )
    links = result.scalars().all()
    components_info = {
        link.role: ComponentInfo(
            id=link.component.id,
            name=link.component.name,
            type=link.component.type,
            provider=link.component.provider,
            entity_config=link.component.entity_config or {}
        ) for link in links
    }
    notifications_enabled = False
    if endpoint:
        from ...core.db_models import PushSubscription
        result = await db.execute(
            select(PrinterNotificationSubscription)
            .join(PushSubscription)
            .where(
                PushSubscription.user_id == user.id,
                PushSubscription.endpoint == endpoint,
                PrinterNotificationSubscription.printer_id == printer_id
            )
        )
        notifications_enabled = result.scalar_one_or_none() is not None

    inference_paused = instance.config.inference_paused
    source = stream_manager.get_source(printer_id)
    if source and source.processor:
        inference_paused = getattr(source.processor, "pause_inference", False)
    return PrinterInfo(
        id=printer_id,
        name=instance.config.name,
        status=status,
        linked_session_id=instance.config.linked_session_id,
        has_control=instance.control is not None,
        has_camera=instance.camera is not None,
        components=components_info,
        inference_sensitivity=instance.config.inference_sensitivity,
        inference_majority_voting=instance.config.inference_majority_voting,
        inference_target_fps=instance.config.inference_target_fps,
        detection_action=instance.config.detection_action,
        notifications_enabled=notifications_enabled,
        inference_paused=inference_paused
    )


@router.post("/{printer_id}/stream", response_model=dict)
async def link_printer_stream(
    printer_id: str, 
    session_id: str = Query(...), 
    settings: Optional[FeedSettings] = None, 
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write", "rtc:stream"])
) -> dict:
    """Ensure printer camera is multiplexed and active."""
    instance = await _get_or_create_printer_instance(printer_id, db)
    if not instance:
        raise HTTPException(status_code=404, detail="Printer not found")

    if settings is None:
        settings = FeedSettings(
            sensitivity=instance.config.inference_sensitivity,
            majority_voting=instance.config.inference_majority_voting,
            target_fps=instance.config.inference_target_fps,
            detection_action=instance.config.detection_action,
            inference_paused=instance.config.inference_paused
        )
    
    if not instance.camera:
        raise HTTPException(status_code=400, detail="Printer has no camera source")
    
    source = stream_manager.get_source(printer_id)
    if source:
        logger.info(f"Syncing settings for existing stream {printer_id}: sensitivity={instance.config.inference_sensitivity}, target_fps={instance.config.inference_target_fps}")
        source.settings.sensitivity = instance.config.inference_sensitivity
        source.settings.majority_voting = instance.config.inference_majority_voting
        source.settings.target_fps = instance.config.inference_target_fps
        source.settings.detection_action = instance.config.detection_action
        source.processor.settings = source.settings
            
        stream_manager.add_alias(printer_id, session_id)
        return {"status": "success", "session_id": session_id, "multiplexed": True}
    
    track, pc = await instance.camera.get_camera_track()
    if not track:
        result = await db.execute(
            select(Printer).where(Printer.id == printer_id).options(
                selectinload(Printer.component_links)
                .joinedload(PrinterComponentLink.component)
            )
        )
        db_p = result.scalar_one_or_none()
        if db_p:
            for link in db_p.component_links:
                if link.role == "camera":
                    db_comp = link.component
                    if db_comp.provider == "webcam" and db_comp.entity_config.get("type") == "browser":
                        owner_id = db_comp.entity_config.get("owner_id")
                        if owner_id:
                            from ...services.notifications import notify_user_camera_access
                            await notify_user_camera_access(owner_id, db_comp.name or instance.config.name)
                    break
        
        raise HTTPException(status_code=404, detail="Camera track not available")
    
    model_info = get_model()
    processor = await start_track_processing(track, predict, model_info, settings, session_id)
    
    from .printer import trigger_printer_action
    from ...services.notifications import notify_defect
    async def on_defect(class_name: str, confidence: float, screenshot_path: str = None):
        if settings.detection_action and settings.detection_action != "none":
            await trigger_printer_action(printer_id, settings.detection_action)
        from ...core.database import async_session as SessionLocal
        async with SessionLocal() as db_session:
            res = await db_session.execute(select(Printer).where(Printer.id == printer_id))
            db_p = res.scalar_one_or_none()
            if db_p:
                db_p.inference_paused = True
                await db_session.commit()
        
        notify_defect(printer_id, class_name, confidence, screenshot_path)
    
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
        stream_manager.add_alias(printer_id, session_id)
    
    instance.config.linked_session_id = session_id
    return {"status": "success", "session_id": session_id}


@router.delete("/{printer_id}")
async def remove_printer(
    printer_id: str, 
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["admin"])
) -> dict:
    """Remove a printer."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    db_printer = result.scalar_one_or_none()
    if not db_printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    await db.delete(db_printer)
    await db.commit()
    if printer_id in _printers:
        _printers.pop(printer_id)
    return {"status": "removed", "id": printer_id}


@router.post("/{printer_id}/{command}")
async def printer_command(
    printer_id: str, 
    command: str, 
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write"])
) -> dict:
    """Send command to printer."""
    instance = await _get_or_create_printer_instance(printer_id, db)
    if not instance:
        raise HTTPException(status_code=404, detail="Printer not found")
    if not instance.control:
        raise HTTPException(status_code=400, detail="Printer does not support control")
    if command == "start": await instance.control.start()
    elif command == "pause": await instance.control.pause()
    elif command == "resume": await instance.control.resume()
    elif command == "stop": await instance.control.stop()
    else: raise HTTPException(status_code=400, detail="Invalid command")
    return {"status": "ok", "command": command}


@router.post("/{printer_id}/inference/{action}")
async def printer_inference_command(
    printer_id: str,
    action: str,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write"])
) -> dict:
    """Start or stop inference for a printer."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    db_printer = result.scalar_one_or_none()
    if not db_printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    paused = action == "stop"
    db_printer.inference_paused = paused
    await db.commit()

    if printer_id in _printers:
        _printers[printer_id].config.inference_paused = paused

    source = stream_manager.get_source(printer_id)
    if source and source.processor:
        source.processor.pause_inference = paused

    return {"status": "ok", "action": action, "inference_paused": paused}
