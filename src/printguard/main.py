"""FastAPI application entry point."""

import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from .core.config import get_settings
from .core.model import download_model, load_model
from .core.database import init_db
from .api.routes import router
from .api.routes.ws import router as ws_router
from .services.webrtc import cleanup
from .services.tunnel_manager import setup_active_tunnel
from .services.storage import screenshot_manager
from .services.auto_detection import auto_detection_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(message)s',
)
logging.getLogger("printguard").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Download model on startup if needed, then load it, sets up tunnel based on configuration and cleans up on shutdown."""
    logger = logging.getLogger("printguard")
    logger.info("Starting PrintGuard service...")
    
    settings = get_settings()
    # Initialize database
    await init_db()
    # Download PrintGuard model
    download_model()
    load_model()
    # Setup tunnel (only one will be activated)
    await setup_active_tunnel(app, settings)

    # Initial screenshot cleanup
    screenshot_manager.cleanup()

    # Background cleanup task
    async def periodic_cleanup():
        while True:
            settings = get_settings()
            await asyncio.sleep(settings.screenshot_cleanup_interval_minutes * 60)
            logger.info("Running periodic screenshot cleanup...")
            screenshot_manager.cleanup()

    cleanup_task = asyncio.create_task(periodic_cleanup())
    auto_detection_task = asyncio.create_task(auto_detection_monitor())

    yield
    
    # Cancel background task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    auto_detection_task.cancel()
    try:
        await auto_detection_task
    except asyncio.CancelledError:
        pass

    # Final cleanup on exit
    screenshot_manager.cleanup()

    # Cleanup tunnel process if it exists
    if hasattr(app.state, "tunnel_process"):
        process = app.state.tunnel_process
        if process:
            print(f"Stopping tunnel process (PID: {process.pid})...")
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
    # Cleanup WebRTC resources
    await cleanup()


app = FastAPI(
    title="PrintGuard API",
    description="Print defect detection API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api")
app.include_router(ws_router, prefix="/api")

webui_dist = os.path.join(os.getcwd(), "webui", "dist")
if os.path.exists(webui_dist):
    app.mount("/", StaticFiles(directory=webui_dist, html=True), name="webui")

@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Serve a screenshot from memory or an expired placeholder."""
    data = screenshot_manager.get(filename)
    if data:
        return Response(content=data, media_type="image/jpeg")
    # Serve placeholder for expired screenshots
    placeholder_io = screenshot_manager.get_expired_placeholder()
    return Response(content=placeholder_io.getvalue(), media_type="image/jpeg")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors gracefully, especially with binary/encrypted data."""
    details = []
    for error in exc.errors():
        if "input" in error and isinstance(error["input"], bytes):
            error["input"] = "<binary data>"
        details.append(error)
    return JSONResponse(
        status_code=422,
        content={"detail": details},
    )
