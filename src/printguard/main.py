"""FastAPI application entry point."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api.routes import router
from .core.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PrintGuard API",
    description="Print defect detection API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
