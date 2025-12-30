"""Printer control endpoints."""

import logging
from typing import Optional, Annotated
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
from ...services.webrtc import start_track_processing
from ...services.streams import stream_manager
from ...services.printer_service import (
    get_instance,
    set_inference_state,
    execute_command,
    handle_defect,
    sync_settings,
    invalidate_cache
)
from ..crypto_utils import EncryptedRoute
from ..auth_utils import get_current_identity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/printer", tags=["printer"], route_class=EncryptedRoute)

def _components_dict(components) -> dict:
    """
    Convert PrinterComponents (which may have extra keys like 'control:stop') into a dict.
    """
    if components is None:
        return {}
    if isinstance(components, dict):
        return {k: v for k, v in components.items() if v is not None}
    if hasattr(components, "model_dump"):
        return {k: v for k, v in components.model_dump(exclude_none=True).items() if v is not None}
    return {k: getattr(components, k) for k in dir(components) if not k.startswith("_")}


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
        detection_action=config.detection_action,
        inference_paused=config.inference_paused,
        auto_detection=config.auto_detection
    )
    if config.id:
        db_printer.id = config.id
    db.add(db_printer)
    await db.flush()
    for role, comp_data in _components_dict(config.components).items():
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
    if getattr(config, "auto_detection", None) is not None:
        db_printer.auto_detection = config.auto_detection
        
    if config.components is not None:
        for link in db_printer.component_links:
            await db.delete(link)
        await db.flush()
        for role, comp_id in _components_dict(config.components).items():
            if not comp_id:
                continue
            res = await db.execute(select(Component).where(Component.id == comp_id))
            if not res.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"Component {comp_id} not found")
            db.add(
                PrinterComponentLink(
                    printer_id=db_printer.id,
                    component_id=comp_id,
                    role=role
                )
            )
            
    await db.commit()
    invalidate_cache(printer_id)
    sync_settings(
        printer_id,
        db_printer.inference_sensitivity,
        db_printer.inference_majority_voting,
        db_printer.inference_target_fps,
        db_printer.detection_action
    )

    return await get_printer(printer_id, db, user)


@router.get("", response_model=list[PrinterInfo])
async def list_printers(
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:read"]),
    endpoint: Annotated[Optional[str], Query()] = None
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
    endpoint: Annotated[Optional[str], Query()] = None
) -> PrinterInfo:
    """Get printer status."""
    instance = await get_instance(printer_id, db)
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
        available_commands=instance.available_commands,
        has_camera=instance.camera is not None,
        components=components_info,
        inference_sensitivity=instance.config.inference_sensitivity,
        inference_majority_voting=instance.config.inference_majority_voting,
        inference_target_fps=instance.config.inference_target_fps,
        detection_action=instance.config.detection_action,
        notifications_enabled=notifications_enabled,
        inference_paused=inference_paused,
        auto_detection=getattr(instance.config, "auto_detection", False)
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
    instance = await get_instance(printer_id, db)
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
        sync_settings(
            printer_id,
            instance.config.inference_sensitivity,
            instance.config.inference_majority_voting,
            instance.config.inference_target_fps,
            instance.config.detection_action
        )
            
        stream_manager.add_alias(printer_id, session_id)
        return {"status": "success", "session_id": session_id, "multiplexed": True}
    
    track, pc = await instance.camera.get_camera_track()
    if not track:
        result = await db.execute(
            select(Printer).where(Printer.id == printer_id).options(
                selectinload(PrinterComponentLink.component)
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
    
    from ...services.notifications import notify_user_camera_access
    model_info = get_model()
    processor = await start_track_processing(track, predict, model_info, settings, session_id)
    processor.printer_id = printer_id

    async def on_defect(class_name: str, confidence: float, screenshot_path: str = None):
        await handle_defect(
            printer_id=printer_id,
            session_id=session_id,
            class_name=class_name,
            confidence=confidence,
            screenshot_path=screenshot_path,
            detection_action=settings.detection_action
        )

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
    invalidate_cache(printer_id)
    return {"status": "removed", "id": printer_id}


@router.post("/{printer_id}/{command}")
async def printer_command(
    printer_id: str, 
    command: str, 
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write"])
) -> dict:
    """Send command to printer."""
    try:
        return await execute_command(printer_id, command, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{printer_id}/inference/{action}")
async def printer_inference_command(
    printer_id: str,
    action: str,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write"])
) -> dict:
    """Start or stop inference for a printer."""
    running = action == "start"
    await set_inference_state(printer_id, running, db)
    return {"status": "ok", "action": action, "inference_paused": not running}
