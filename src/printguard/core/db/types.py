import enum

class ConnectionType(str, enum.Enum):
    OCTOPRINT = "octoprint"
    HOMEASSISTANT = "homeassistant"
    BAMBULABS = "bambulabs"
    LOCAL = "local"

class ComponentType(str, enum.Enum):
    CAMERA = "camera"
    CONTROL = "control"
    STATUS = "status"

class IdentityType(str, enum.Enum):
    USER = "user"
    SERVICE = "service"

class ScopeType(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"