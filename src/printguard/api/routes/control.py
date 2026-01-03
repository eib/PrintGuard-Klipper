"""Control component trigger route."""
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.types import ComponentType
from ...core.security.jwt import TokenData
from ...core.connections import get_connection_instance

router = APIRouter(prefix="/control")


class TriggerResponse(BaseModel):
    success: bool
    component_id: uuid.UUID


@router.post("/{component_id}/trigger", response_model=TriggerResponse)
async def trigger_control(
    component_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Trigger a control component (e.g., start/stop print)."""
    component = await services.components.get_full(component_id)
    if not component:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    if component.type != ComponentType.CONTROL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Component is type '{component.type}', expected 'control'"
        )
    
    connection = await services.connections.get(component.connection_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    
    conn_instance = get_connection_instance(connection, services)
    if not conn_instance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported connection provider")
    
    entity_id = component.config.get("entity_id")
    if not entity_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Component missing entity_id config")
    
    success = await conn_instance.trigger_control(entity_id)
    return TriggerResponse(success=success, component_id=component_id)
