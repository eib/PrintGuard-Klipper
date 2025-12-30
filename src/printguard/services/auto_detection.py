"""Automatic start/stop of inference based on printer status."""

import asyncio
import logging
from typing import Dict

import httpx
from sqlalchemy import select

from ..core.database import async_session
from ..core.db_models import Printer, PrinterComponentLink
from .printer_service import get_instance, start_stream, stop_stream

logger = logging.getLogger(__name__)


async def auto_detection_monitor(poll_interval_s: float = 5.0) -> None:
    """Poll printers with auto-detection and start/stop streams based on print status."""
    last_printing: Dict[str, bool] = {}

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
                        instance = await get_instance(pid, db)
                        if not instance or not instance.status:
                            continue
                        is_printing = await instance.status.is_printing()
                    except (httpx.ReadTimeout, httpx.TimeoutException, httpx.ConnectTimeout):
                        logger.warning("Auto-detection: timeout for %s", pid)
                        continue
                    except Exception:
                        logger.debug("Auto-detection: failed for %s", pid, exc_info=True)
                        continue

                    prev = last_printing.get(pid)
                    if is_printing and (prev is None or not prev):
                        await start_stream(pid, db)
                    elif not is_printing and prev:
                        await stop_stream(pid)

                    last_printing[pid] = is_printing

                for stale in set(last_printing.keys()) - set(printer_ids):
                    last_printing.pop(stale, None)

        except Exception:
            logger.debug("Auto-detection: loop error", exc_info=True)

        await asyncio.sleep(poll_interval_s)
