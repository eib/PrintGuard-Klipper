"""FastAPI application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from .api.routes import router
from .core.db.session import init_db, get_session_ctx
from .core.config import settings
from .core.redis_client import init_redis, close_redis, redis_subscriber
from .core.ml.model import download_model, load_model
from .core.worker import worker_orchestrator
from .core.notifications.vapid import ensure_vapid_configured
from .core.security.jwt_secret import ensure_jwt_secret


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure JWT secret exists (auto-generates if not configured)
    ensure_jwt_secret()

    # Ensure Web Push VAPID keys exist (stored in WEBPUSH_VAPID_KEYS_PATH)
    ensure_vapid_configured()

    # Initialize Redis
    await init_redis()
    
    # Start Redis Pub/Sub listener
    from .core.state.manager import ws_manager
    subscriber_task = asyncio.create_task(redis_subscriber(ws_manager))
    
    # Initialize Database
    await init_db()

    # Download and load ML model
    download_model()
    load_model()

    # Sync cameras on startup
    from .core.stream_manager import StreamManager
    async with get_session_ctx() as services:
        stream_manager = StreamManager(services)
        try:
            await stream_manager.sync_cameras()
        except Exception as e:
            print(f"Failed to sync cameras on startup: {e}")

    # Start background workers
    await worker_orchestrator.start()

    yield
    
    # Cleanup
    await worker_orchestrator.stop()
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await close_redis()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
