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
