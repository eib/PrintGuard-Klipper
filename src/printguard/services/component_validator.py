"""Centralized validation for printer components and their associated entities."""

# Mapping of component types to allowed entity domains
ALLOWED_DOMAINS = {
    "camera": ["camera"],
    "status": ["sensor", "binary_sensor"],
    "control": ["button", "switch"]
}

def get_allowed_domains(component_type: str) -> list[str]:
    """Return the list of allowed entity domains for a given component type."""
    return ALLOWED_DOMAINS.get(component_type, [])

def get_entity_domain(entity_id: str) -> str:
    """Extract the domain from an entity ID (e.g. 'camera.living_room' -> 'camera')."""
    if not entity_id or "." not in entity_id:
        return ""
    return entity_id.split(".")[0].lower()

def is_valid_entity(component_type: str, entity_id: str) -> bool:
    """Check if an entity ID is valid for the given component type."""
    domain = get_entity_domain(entity_id)
    allowed = get_allowed_domains(component_type)
    return domain in allowed

def get_component_type_from_entity(entity_id: str) -> str | None:
    """Determine the PrintGuard component type for a given entity domain."""
    domain = get_entity_domain(entity_id)
    for comp_type, domains in ALLOWED_DOMAINS.items():
        if domain in domains:
            return comp_type
    return None

