"""Component management routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.components import ComponentCreate, ComponentRead, ComponentUpdate
from ...core.security.jwt import TokenData

router = APIRouter(prefix="/components")


@router.get("/", response_model=list[ComponentRead])
async def list_components(
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """List all components with their connections."""
    return await services.components.list_full()


@router.get("/{component_id}", response_model=ComponentRead)
async def get_component(
    component_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Get a single component by ID."""
    component = await services.components.get_full(component_id)
    if not component:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    return component


@router.post("/", response_model=ComponentRead, status_code=status.HTTP_201_CREATED)
async def create_component(
    data: ComponentCreate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Create a new component."""
    connection = await services.connections.get(data.connection_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection not found")
    component = await services.components.create(data)
    return await services.components.get_full(component.id)


@router.patch("/{component_id}", response_model=ComponentRead)
async def update_component(
    component_id: uuid.UUID,
    data: ComponentUpdate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Update a component's configuration."""
    existing = await services.components.get(component_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    if "config" in update_data and update_data["config"]:
        update_data["config"] = update_data["config"].model_dump() if hasattr(update_data["config"], "model_dump") else update_data["config"]
    await services.components.update(component_id, update_data)
    return await services.components.get_full(component_id)


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(
    component_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Delete a component."""
    existing = await services.components.get(component_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    await services.components.delete(component_id)
