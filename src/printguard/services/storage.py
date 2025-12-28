import time
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class ScreenshotManager:
    """In-memory storage for screenshots using a dictionary."""
    
    def __init__(self):
        self._storage = {}

    def add(self, filename: str, data: bytes):
        """Add a new screenshot and enforce max count."""
        settings = get_settings()
        now = time.time()
        self._storage[filename] = (now, data)
        while len(self._storage) > settings.screenshot_max_count:
            oldest_key = next(iter(self._storage))
            del self._storage[oldest_key]
            logger.debug(f"Removed oldest screenshot from memory: {oldest_key}")

    def get(self, filename: str) -> bytes | None:
        """Retrieve screenshot bytes."""
        entry = self._storage.get(filename)
        return entry[1] if entry else None

    def cleanup(self):
        """Remove entries older than retention_hours."""
        settings = get_settings()
        now = time.time()
        retention_threshold = now - (settings.screenshot_retention_hours * 3600)
        expired_keys = [
            k for k, (t, _) in self._storage.items() 
            if t < retention_threshold
        ]
        for k in expired_keys:
            del self._storage[k]
            logger.info(f"Cleaned up expired memory screenshot: {k}")

    def get_expired_placeholder(self) -> BytesIO:
        """Generate a 640x480 'Screenshot Expired' image using PIL."""
        img = Image.new('RGB', (640, 480), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        text = "Screenshot Expired"
        try:
            font = ImageFont.load_default()
        except:
            font = None
        draw.text((220, 230), text, fill=(200, 200, 200), font=font)
        subtext = "Cleaned up according to retention policy"
        draw.text((180, 260), subtext, fill=(150, 150, 150), font=font)
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=80)
        img_io.seek(0)
        return img_io

screenshot_manager = ScreenshotManager()

def cleanup_screenshots():
    """Legacy wrapper for compatibility."""
    screenshot_manager.cleanup()
