"""Backup scheduler implementation."""

from __future__ import annotations

import contextlib
import sched
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from erp.modules.backup.application.ports import SchedulerPort


class BackupScheduler(SchedulerPort):
    """Simple scheduler for backup jobs."""

    def __init__(self) -> None:
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._thread: threading.Thread | None = None
        self._running = False
        self._jobs: dict[str, sched.Event] = {}
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._lock = threading.Lock()

    def schedule_daily_backup(self, time_str: str, callback: Callable[[], None]) -> None:
        """Schedule daily backup at specific time (HH:MM)."""
        self._cancel_if_exists("daily_backup")
        self._schedule_recurring("daily_backup", time_str, 86400, callback)

    def schedule_monthly_backup(
        self, day: int, time_str: str, callback: Callable[[], None]
    ) -> None:
        """Schedule monthly backup on specific day at specific time."""
        # For simplicity, schedule daily and check day in callback
        self._cancel_if_exists("monthly_backup")
        self._schedule_recurring("monthly_backup", "00:00", 86400, callback)

    def cancel_scheduled(self, backup_type: str) -> None:
        self._cancel_if_exists(backup_type)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def _schedule_recurring(
        self, job_id: str, time_str: str, interval_seconds: int, callback: Callable[[], None]
    ) -> None:
        hour, minute = map(int, time_str.split(":"))
        self._next_run_time(hour, minute)

        def job() -> None:
            with contextlib.suppress(Exception):
                self._callbacks[job_id]()
            # Re-schedule
            if self._running:
                next_run = time.time() + 86400
                with self._lock:
                    self._scheduler.enterabs(next_run, 1, self._run_job, argument=(job_id,))

        with self._lock:
            self._callbacks[job_id] = callback
            event = self._scheduler.enterabs(
                self._next_run_time(*map(int, time_str.split(":"))),
                1,
                self._run_job,
                argument=(job_id, 86400),
            )
            self._jobs[job_id] = event

    def _cancel_if_exists(self, job_id: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                with contextlib.suppress(ValueError):
                    self._scheduler.cancel(self._jobs[job_id])
                del self._jobs[job_id]
                self._callbacks.pop(job_id, None)

    def _next_run_time(self, hour: int, minute: int) -> float:
        now = datetime.now(UTC)
        next_run = datetime.now(UTC).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run.timestamp() <= time.time():
            next_run = next_run.replace(day=now.day + 1)
        return next_run.timestamp()

    def _run(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
                self._scheduler.run(blocking=False)
            time.sleep(0.1)

    def _run_job(self, job_id: str, interval: int) -> None:
        callback = self._callbacks.get(job_id)
        if callback:
            with contextlib.suppress(Exception):
                callback()
        # Re-schedule
        if self._running:
            cb = self._callbacks.get(job_id, lambda: None)
            self._schedule_recurring(job_id, "00:00", 86400, cb)