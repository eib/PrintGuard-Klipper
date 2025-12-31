"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.routes import router


app = FastAPI(
    title="PrintGuard API",
    description="Print defect detection API",
    version="1.0.0",
)

app.include_router(router, prefix="/api")


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
