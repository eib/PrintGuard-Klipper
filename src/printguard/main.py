"""FastAPI application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from .api.routes import router
from .core.db.session import init_db
from .core.config import settings
from .core.redis_client import init_redis, close_redis, redis_subscriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Redis
    await init_redis()
    
    # Start Redis Pub/Sub listener
    from .core.state.manager import ws_manager
    subscriber_task = asyncio.create_task(redis_subscriber(ws_manager))
    
    # Initialize Database
    await init_db()

    # Sync cameras on startup
    from .core.db.session import AsyncSessionLocal, ServiceManager
    from .core.state.manager import state_manager
    from .core.stream_manager import StreamManager
    async with AsyncSessionLocal() as session:
        service_manager = ServiceManager(session, state_manager)
        stream_manager = StreamManager(service_manager)
        try:
            await stream_manager.sync_cameras()
        except Exception as e:
            print(f"Failed to sync cameras on startup: {e}")
    yield
    
    # Cleanup
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
