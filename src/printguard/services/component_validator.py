"""Centralized validation for printer components and their associated entities."""

# Mapping of component types to allowed entity domains
ALLOWED_DOMAINS = {
    "camera": ["camera"],
    "status": ["sensor", "binary_sensor", "input_select"],
    "control": ["button", "switch", "input_button", "input_boolean"]
}

# Default state values for Home Assistant status components
DEFAULT_STATE_VALUES = {
    "printing_state": "printing",
    "paused_state": "paused",
    "error_state": "error"
}

def get_default_state_value(state_type: str) -> str:
    """Return the default value for a given state type."""
    return DEFAULT_STATE_VALUES.get(state_type, "")

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

def is_camera_entity(entity_id: str) -> bool:
    """Check if an entity ID is a camera component."""
    return is_valid_entity("camera", entity_id)

def is_status_entity(entity_id: str) -> bool:
    """Check if an entity ID is a status component."""
    return is_valid_entity("status", entity_id)

def is_control_entity(entity_id: str) -> bool:
    """Check if an entity ID is a control component."""
    return is_valid_entity("control", entity_id)

