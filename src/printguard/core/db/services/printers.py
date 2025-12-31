import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from . import BaseService
from ..schemas.tables.printers import Printer
from ..schemas.interactions.printers import PrinterCreate

class PrinterService(BaseService[Printer, PrinterCreate]):
    def __init__(self, session: AsyncSession):
        super().__init__(Printer, session)

    async def get_printer_details(self, printer_id: uuid.UUID) -> Optional[Printer]:
        return await self.get(printer_id, load_relations=[
            Printer.camera_component,
            Printer.status_component,
            Printer.start_control,
            Printer.stop_control
        ])

    async def list_printers_details(self) -> List[Printer]:
        return await self.list(load_relations=[
            Printer.camera_component,
            Printer.status_component,
            Printer.start_control,
            Printer.stop_control
        ])