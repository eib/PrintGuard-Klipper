"""FastAPI application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api.routes import router
from .core.db.session import init_db
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
