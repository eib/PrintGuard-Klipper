from typing import Any, Dict, Optional

import requests

from ...models import JobInfoResponse, PrinterState, PrinterTemperatures, Progress


class MoonrakerClient:
    """A lightweight client for Moonraker printer control and status."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-Api-Key"] = api_key

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict:
        response = requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self.headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_printer_state(self) -> PrinterState:
        data = self._request(
            "GET",
            "/printer/objects/query?print_stats&extruder&heater_bed"
        )
        status = data.get("result", {}).get("status", {})
        print_stats = status.get("print_stats", {})
        extruder = status.get("extruder", {})
        bed = status.get("heater_bed", {})

        state_raw = (print_stats.get("state") or "standby").lower()
        state_map = {
            "printing": "Printing",
            "paused": "Paused",
            "complete": "Operational",
            "standby": "Operational",
            "cancelled": "Cancelled",
            "error": "Error",
        }
        state = state_map.get(state_raw, state_raw.title())

        filename = print_stats.get("filename")
        progress = Progress(completion=None, filepos=None, printTime=None, printTimeLeft=None)
        job_info = JobInfoResponse(
            job={"file": {"name": filename} if filename else {}},
            progress=progress,
            state=state,
            error=None,
        )

        printer_temps = PrinterTemperatures(
            nozzle_actual=extruder.get("temperature"),
            nozzle_target=extruder.get("target"),
            bed_actual=bed.get("temperature"),
            bed_target=bed.get("target"),
        )

        return PrinterState(jobInfoResponse=job_info, temperatureReading=printer_temps)

    def get_job_info(self) -> JobInfoResponse:
        return self.get_printer_state().jobInfoResponse

    def pause_job(self) -> None:
        self._request("POST", "/printer/print/pause")

    def cancel_job(self) -> None:
        self._request("POST", "/printer/print/cancel")
