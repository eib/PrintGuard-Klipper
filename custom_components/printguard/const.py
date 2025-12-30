"""Constants for the PrintGuard integration."""

DOMAIN = "printguard"

# Server configuration
CONF_URL = "url"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_TOKEN = "token"
CONF_CONNECTION_ID = "connection_id"

# Status mapping
CONF_PRINTING_STATES = "printing_states"
CONF_PAUSED_STATES = "paused_states"
CONF_ERROR_STATES = "error_states"

# Component entity references
CONF_CAMERA = "camera"
CONF_START_ENTITY = "start_entity"
CONF_PAUSE_ENTITY = "pause_entity"
CONF_RESUME_ENTITY = "resume_entity"
CONF_STOP_ENTITY = "stop_entity"
CONF_PRINTER_NAME = "printer_name"

# Mapping of component types to allowed entity domains
ALLOWED_DOMAINS = {
    "camera": ["camera"],
    "status": ["sensor", "binary_sensor", "input_select"],
    "control": ["button", "switch", "input_button", "input_boolean"]
}

# Polling interval (seconds)
SCAN_INTERVAL_SECONDS = 10

# Crypto configuration
CONF_SERVER_PUBLIC_KEY = "server_public_key"
CONF_CLIENT_PRIVATE_KEY = "client_private_key"
CONF_CLIENT_PUBLIC_KEY = "client_public_key"

# Events
EVENT_DEFECT_DETECTED = f"{DOMAIN}_defect_detected"

# Platforms to set up
PLATFORMS = ["sensor", "binary_sensor", "button", "camera", "event"]
