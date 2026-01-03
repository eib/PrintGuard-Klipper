"""Camera stream URL route."""
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.types import ComponentType
from ...core.security.jwt import TokenData
from ...core.connections import get_connection_instance

router = APIRouter(prefix="/streams")


class StreamUrlResponse(BaseModel):
    component_id: uuid.UUID
    stream_url: str


@router.get("/{component_id}", response_model=StreamUrlResponse)
async def get_stream_url(
    component_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Get the stream URL for a camera component."""
    component = await services.components.get_full(component_id)
    if not component:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    if component.type != ComponentType.CAMERA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Component is type '{component.type}', expected 'camera'"
        )
    
    connection = await services.connections.get(component.connection_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    
    conn_instance = get_connection_instance(connection, services)
    if not conn_instance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported connection provider")
    
    try:
        stream_url = await conn_instance.get_stream_url(component)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return StreamUrlResponse(component_id=component_id, stream_url=stream_url)
