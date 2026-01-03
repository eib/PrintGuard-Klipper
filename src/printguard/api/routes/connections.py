"""Connection management routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.connections import ConnectionCreate, ConnectionRead, ConnectionUpdate
from ...core.security.jwt import TokenData

router = APIRouter(prefix="/connections")


@router.get("/", response_model=list[ConnectionRead])
async def list_connections(
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """List all connections."""
    return await services.connections.list()


@router.get("/{connection_id}", response_model=ConnectionRead)
async def get_connection(
    connection_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Get a single connection by ID."""
    connection = await services.connections.get(connection_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return connection


@router.post("/", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Create a new connection."""
    return await services.connections.create(data)


@router.patch("/{connection_id}", response_model=ConnectionRead)
async def update_connection(
    connection_id: uuid.UUID,
    data: ConnectionUpdate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Update an existing connection."""
    existing = await services.connections.get(connection_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    await services.connections.update(connection_id, update_data)
    return await services.connections.get(connection_id)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Delete a connection."""
    existing = await services.connections.get(connection_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    await services.connections.delete(connection_id)
