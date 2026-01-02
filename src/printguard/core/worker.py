"""Background worker orchestrator for polling and inference tasks."""

import asyncio
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from .config import settings
from .state.manager import state_manager
from .state.models import InferenceResult, InferenceClass
from .stream_manager import StreamManager
from .db.session import get_session_ctx
from .connections import get_connection_instance
from .ml.inference import predict
from .ml.model import load_model


logger = logging.getLogger(__name__)


class WorkerOrchestrator:
    """Manages background polling and inference tasks."""

    def __init__(self):
        self.stop_event = asyncio.Event()
        self.inference_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCES)
        self.tasks: List[asyncio.Task] = []
        self.model_info: Optional[dict] = None

    async def start(self) -> List[asyncio.Task]:
        """Start all background worker tasks."""
        self.model_info = load_model()
        self.tasks = [
            asyncio.create_task(self._connection_health_loop()),
            asyncio.create_task(self._printer_status_loop()),
            asyncio.create_task(self._inference_orchestrator_loop()),
        ]
        logger.info("Worker orchestrator started")
        return self.tasks

    async def stop(self):
        """Signal all tasks to stop gracefully."""
        self.stop_event.set()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Worker orchestrator stopped")

    async def _wait_interval(self, interval: float):
        """Wait for interval or until stop is signaled."""
        try:
            await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass

    async def _connection_health_loop(self):
        """Periodically check connection health."""
        while not self.stop_event.is_set():
            try:
                async with get_session_ctx() as services:
                    connections = await services.connections.list()
                    for conn in connections:
                        try:
                            connection = get_connection_instance(conn, services)
                            if connection:
                                is_healthy = await connection.is_healthy()
                                await state_manager.update_connection_state(conn.id, is_healthy)
                        except Exception as e:
                            logger.error(f"Health check failed for connection {conn.id}: {e}")
                            await state_manager.update_connection_state(conn.id, False)
            except Exception as e:
                logger.error(f"Connection health loop error: {e}")
            await self._wait_interval(settings.CONNECTION_HEALTH_INTERVAL)

    async def _printer_status_loop(self):
        """Periodically poll printer status from connections."""
        while not self.stop_event.is_set():
            try:
                async with get_session_ctx() as services:
                    printers = await services.printers.list_printers_details()
                    # Group by connection
                    by_connection: dict[uuid.UUID, list] = {}
                    for printer in printers:
                        if printer.status_component:
                            conn_id = printer.status_component.connection_id
                            by_connection.setdefault(conn_id, []).append(printer)
                    for conn_id, printer_list in by_connection.items():
                        try:
                            conn = await services.connections.get(conn_id)
                            if not conn:
                                continue
                            connection = get_connection_instance(conn, services)
                            if not connection:
                                continue
                            status_ids = [p.status_component.entity_id for p in printer_list]
                            states = await connection.get_status_states(status_ids)
                            for printer, state_str in zip(printer_list, states):
                                status = connection.map_status_state(state_str)
                                await state_manager.update_printer_state(printer.id, status=status)
                        except Exception as e:
                            logger.error(f"Status poll failed for connection {conn_id}: {e}")
            except Exception as e:
                logger.error(f"Printer status loop error: {e}")
            await self._wait_interval(settings.PRINTER_STATUS_INTERVAL)

    async def _inference_orchestrator_loop(self):
        """Single orchestrator that schedules inference for active printers."""
        while not self.stop_event.is_set():
            try:
                active_printer_ids = await state_manager.get_active_detection_printer_ids()
                if active_printer_ids:
                    async with get_session_ctx() as services:
                        tasks = []
                        for printer_id in active_printer_ids:
                            printer = await services.printers.get_printer_details(printer_id)
                            if printer and printer.camera_component:
                                camera_path = str(printer.camera_component.id)
                                tasks.append(self._run_single_inference(printer_id, camera_path, services))
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Inference orchestrator error: {e}")
            await self._wait_interval(settings.DETECTION_INTERVAL)

    async def _run_single_inference(self, printer_id: uuid.UUID, camera_path: str, services):
        """Run inference for a single printer with semaphore control."""
        async with self.inference_semaphore:
            try:
                stream_manager = StreamManager(services)
                snapshot = await stream_manager.get_snapshot(camera_path)
                if snapshot is None:
                    logger.warning(f"No snapshot for printer {printer_id}")
                    return
                result = await asyncio.to_thread(predict, snapshot, self.model_info)
                inference_result = InferenceResult(
                    class_name=InferenceClass(result["class_name"]),
                    confidence=result["confidence"],
                    timestamp=datetime.now(),
                )
                await state_manager.update_printer_state(printer_id, inference_result=inference_result)
            except Exception as e:
                logger.error(f"Inference failed for printer {printer_id}: {e}", exc_info=True)


worker_orchestrator = WorkerOrchestrator()
