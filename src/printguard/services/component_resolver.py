"""Centralized component resolution logic."""

import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db_models import Component, Connection
from ..providers import get_provider

logger = logging.getLogger(__name__)


async def resolve_component(comp: Component, db: AsyncSession) -> Any:
    """Instantiate a provider component from DB model.
    
    Args:
        comp: Component database model
        db: Database session
        
    Returns:
        Instantiated provider or None if failed
    """
    provider = comp.provider
    config = {}
    
    if comp.connection_id:
        if not comp.connection:
            res = await db.execute(
                select(Connection).where(Connection.id == comp.connection_id)
            )
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
        logger.error(f"Failed to instantiate provider {provider}: {e}")
        return None


def build_component_config(comp: Component) -> dict:
    """Build merged config from component and its connection.
    
    Args:
        comp: Component with optionally loaded connection
        
    Returns:
        Merged configuration dictionary
    """
    config = {}
    if comp.connection:
        config.update(comp.connection.config)
    config.update(comp.entity_config or {})
    return config

