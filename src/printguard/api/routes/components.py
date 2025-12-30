import logging
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...core.db_models import Component, PrinterComponentLink
from ...core.models import ComponentCreate, ComponentInfo, FeedSettings
from ...core.model import get_model
from ...core.inference import predict
from ...providers import get_provider
from ...services.webrtc import start_track_processing
from ...services.streams import stream_manager
from ...services.component_resolver import build_component_config
from ...services.component_validator import is_valid_entity
from ..auth_utils import get_current_identity
from ..crypto_utils import EncryptedRoute

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/components", tags=["components"], route_class=EncryptedRoute)

@router.get("", response_model=List[ComponentInfo])
async def list_components(
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:read"]),
    type: Annotated[Optional[str], Query()] = None,
    provider: Annotated[Optional[str], Query()] = None,
    connection_id: Annotated[Optional[str], Query()] = None
):
    """List all components."""
    stmt = select(Component).options(selectinload(Component.connection))
    if type:
        stmt = stmt.where(Component.type == type)
    if provider:
        stmt = stmt.where(Component.provider == provider)
    if connection_id:
        stmt = stmt.where(Component.connection_id == connection_id)
    
    result = await db.execute(stmt)
    components = result.scalars().all()
    return [
        ComponentInfo(
            id=c.id,
            name=c.name,
            type=c.type,
            provider=c.provider,
            entity_config=c.entity_config or {}
        ) for c in components
    ]

@router.get("/{id}", response_model=ComponentInfo)
async def get_component(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:read"])
):
    """Get single component by id."""
    result = await db.execute(select(Component).where(Component.id == id))
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return ComponentInfo(
        id=component.id,
        name=component.name,
        type=component.type,
        provider=component.provider,
        entity_config=component.entity_config or {}
    )

@router.post("", response_model=ComponentInfo)
async def create_component(
    request: ComponentCreate,
    db: AsyncSession = Depends(get_db),
    user: any = Security(get_current_identity, scopes=["printer:write"])
):
    """Create a new component."""
    entity_config = request.entity_config or {}
    
    # 1. Domain Validation (mostly for Home Assistant)
    entity_id = entity_config.get("entity_id")
    if entity_id and "." in entity_id:
        if not is_valid_entity(request.type, entity_id):
            raise HTTPException(
                status_code=400, 
                detail=f"Entity {entity_id} is not valid for component type {request.type}"
            )

    # 2. Cleanup: Handle provider-specific config initialization
    if request.provider == "webcam" and entity_config.get("type") == "browser":
        entity_config["owner_id"] = user.id

    # 3. Provider-specific validation
    prov_cls = get_provider(request.provider)
    if prov_cls:
        full_config = {**entity_config}
        if request.connection_id:
            from ...core.db_models import Connection
            res = await db.execute(select(Connection).where(Connection.id == request.connection_id))
            conn = res.scalar_one_or_none()
            if conn:
                full_config.update(conn.config)
        
        if not await prov_cls.validate_component(full_config):
            raise HTTPException(
                status_code=400, 
                detail=f"Configuration validation failed for provider {request.provider}. Ensure all required fields (like state labels) are provided and the entity exists."
            )

    component = Component(
        name=request.name,
        type=request.type,
        provider=request.provider,
        connection_id=request.connection_id,
        entity_config=entity_config
    )
    db.add(component)
    await db.commit()
    await db.refresh(component)
    return ComponentInfo(
        id=component.id,
        name=component.name,
        type=component.type,
        provider=component.provider,
        entity_config=component.entity_config or {}
    )

@router.delete("/{id}")
async def delete_component(
    id: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write"])
):
    """Delete component."""
    result = await db.execute(
        select(Component)
        .where(Component.id == id)
        .options(selectinload(Component.printer_links))
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    if component.printer_links and not force:
        printer_ids = [link.printer_id for link in component.printer_links]
        raise HTTPException(
            status_code=409, 
            detail={"message": "Component in use by printers", "printers": printer_ids}
        )
    
    await db.delete(component)
    await db.commit()
    return {"status": "success"}

@router.get("/{id}/health")
async def check_component_health(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:read"])
):
    """Test component connection health."""
    result = await db.execute(select(Component).where(Component.id == id).options(selectinload(Component.connection)))
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    prov_cls = get_provider(component.provider)
    if not prov_cls:
        raise HTTPException(status_code=400, detail="Provider not found")
    
    config = build_component_config(component)
    
    is_healthy = await prov_cls.validate_component(config)
    return {"healthy": is_healthy}

@router.get("/{id}/printers")
async def list_component_printers(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:read"])
):
    """List printers using this component."""
    result = await db.execute(select(PrinterComponentLink).where(PrinterComponentLink.component_id == id))
    links = result.scalars().all()
    return [{"printer_id": link.printer_id, "role": link.role} for link in links]

@router.post("/{id}/stream", response_model=dict)
async def link_component_stream(
    id: str, 
    session_id: str = Query(...), 
    settings: FeedSettings = FeedSettings(), 
    db: AsyncSession = Depends(get_db),
    _: any = Security(get_current_identity, scopes=["printer:write", "rtc:stream"])
) -> dict:
    """Ensure component camera is multiplexed and active for preview."""
    result = await db.execute(select(Component).where(Component.id == id).options(selectinload(Component.connection)))
    db_comp = result.scalar_one_or_none()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Component not found")
    
    if db_comp.type != "camera":
        raise HTTPException(status_code=400, detail="Only camera components can be streamed")

    if stream_manager.get_source(id):
        stream_manager.add_alias(id, session_id)
        return {"status": "success", "session_id": session_id, "multiplexed": True}

    prov_cls = get_provider(db_comp.provider)
    if not prov_cls:
        raise HTTPException(status_code=400, detail=f"Provider {db_comp.provider} not found")
    
    config = build_component_config(db_comp)
    
    instance = prov_cls(**config)
    track, pc = await instance.get_camera_track()
    
    if not track:
        if db_comp.provider == "webcam" and db_comp.entity_config.get("type") == "browser":
            owner_id = db_comp.entity_config.get("owner_id")
            if owner_id:
                from ...services.notifications import notify_user_camera_access
                await notify_user_camera_access(owner_id, db_comp.name or "Camera")
        
        raise HTTPException(status_code=404, detail="Camera track not available")
        
    model_info = get_model()
    processor = await start_track_processing(track, predict, model_info, settings, session_id)
    
    if processor.relayed_track:
        await stream_manager.register_source(
            id, 
            processor.relayed_track, 
            processor,
            pc=pc,
            device_name=f"{db_comp.name} Preview",
            settings=settings
        )
        stream_manager.add_alias(id, session_id)
        
    return {"status": "success", "session_id": session_id}

