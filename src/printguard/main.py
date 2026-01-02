"""FastAPI application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api.routes import router
from .core.db.session import init_db
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

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

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
