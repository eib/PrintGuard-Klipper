"""Automatic start/stop of inference based on printer status."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import async_session
from ..core.db_models import Printer, PrinterComponentLink
from ..api.routes.printer import _get_or_create_printer_instance
from .streams import stream_manager

logger = logging.getLogger(__name__)


async def _set_inference_paused(printer_id: str, paused: bool, db: Optional[AsyncSession] = None) -> None:
    """Apply inference pause state to DB, cached instance, and active processor if present.
    
    Args:
        printer_id: ID of the printer
        paused: Whether inference should be paused
        db: Optional database session. If not provided, a new session will be created.
    """
    if db is None:
        async with async_session() as session:
            result = await session.execute(select(Printer).where(Printer.id == printer_id))
            db_printer = result.scalar_one_or_none()
            if not db_printer:
                return
            db_printer.inference_paused = paused
            await session.commit()

            instance = await _get_or_create_printer_instance(printer_id, session)
            if instance:
                instance.config.inference_paused = paused
    else:
        result = await db.execute(select(Printer).where(Printer.id == printer_id))
        db_printer = result.scalar_one_or_none()
        if not db_printer:
            return
        db_printer.inference_paused = paused
        await db.commit()

        instance = await _get_or_create_printer_instance(printer_id, db)
        if instance:
            instance.config.inference_paused = paused

    source = stream_manager.get_source(printer_id)
    if source and source.processor:
        source.processor.pause_inference = paused


async def auto_detection_monitor(poll_interval_s: float = 10.0) -> None:
    """
    Poll printers with auto-detection enabled and toggle inference based on print status.

    Rules:
    - Only operates when a status component is attached.
    - On transition to printing: start inference (paused=False)
    - On transition to not-printing: stop inference (paused=True)
    """
    last_is_printing: Dict[str, bool] = {}

    while True:
        try:
            async with async_session() as db:
                res = await db.execute(
                    select(Printer.id)
                    .join(PrinterComponentLink, PrinterComponentLink.printer_id == Printer.id)
                    .where(Printer.auto_detection == True)  # noqa: E712
                    .where(PrinterComponentLink.role == "status")
                )
                printer_ids = list(res.scalars().all())

                for pid in printer_ids:
                    try:
                        instance = await _get_or_create_printer_instance(pid, db)
                        if not instance or not instance.status:
                            continue
                        is_printing = await instance.status.is_printing()
                    except (httpx.ReadTimeout, httpx.TimeoutException, httpx.ConnectTimeout):
                        logger.warning("Auto-detection: timeout checking status for %s", pid)
                        continue
                    except Exception:
                        logger.debug("Auto-detection: status check failed for %s", pid, exc_info=True)
                        continue

                    prev = last_is_printing.get(pid)
                    if prev is None:
                        last_is_printing[pid] = is_printing
                        continue

                    if is_printing != prev:
                        await _set_inference_paused(pid, paused=not is_printing, db=db)
                        last_is_printing[pid] = is_printing

                for stale in set(last_is_printing.keys()) - set(printer_ids):
                    last_is_printing.pop(stale, None)

        except Exception:
            logger.debug("Auto-detection: monitor loop error", exc_info=True)

        await asyncio.sleep(poll_interval_s)


