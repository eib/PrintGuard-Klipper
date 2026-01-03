"""Printer management routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_services
from ..deps_auth import get_current_identity
from ...core.db.session import ServiceManager
from ...core.db.schemas.interactions.printers import PrinterCreate, PrinterRead, PrinterUpdate
from ...core.security.jwt import TokenData

router = APIRouter(prefix="/printers")


@router.get("/", response_model=list[PrinterRead])
async def list_printers(
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """List all printers with their components."""
    return await services.printers.list_printers_details()


@router.get("/{printer_id}", response_model=PrinterRead)
async def get_printer(
    printer_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Get a single printer by ID."""
    printer = await services.printers.get_printer_details(printer_id)
    if not printer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    return printer


@router.post("/", response_model=PrinterRead, status_code=status.HTTP_201_CREATED)
async def create_printer(
    data: PrinterCreate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Create a new printer."""
    printer = await services.printers.create(data)
    return await services.printers.get_printer_details(printer.id)


@router.patch("/{printer_id}", response_model=PrinterRead)
async def update_printer(
    printer_id: uuid.UUID,
    data: PrinterUpdate,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Update an existing printer."""
    existing = await services.printers.get(printer_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    await services.printers.update(printer_id, update_data)
    return await services.printers.get_printer_details(printer_id)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: uuid.UUID,
    services: ServiceManager = Depends(get_services),
    _: TokenData = Depends(get_current_identity),
):
    """Delete a printer."""
    existing = await services.printers.get(printer_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    await services.printers.delete(printer_id)
