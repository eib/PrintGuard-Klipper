"""FastAPI application entry point."""

from fastapi import FastAPI

from .api.routes import router


app = FastAPI(
    title="PrintGuard API",
    description="Print defect detection API",
    version="1.0.0",
)

app.include_router(router, prefix="/api")
