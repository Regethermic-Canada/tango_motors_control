import logging
import time
from threading import RLock
from typing import Protocol

import flet as ft

from models.motor_types import MotorAction, MotorActionResult
from services.motors.motor_service import (
    MotorService,
    MotorServiceConfig,
    MotorStatusSnapshot,
)
from services.motors.tray_speed import (
    clamp_sec_per_tray,
    sec_per_tray_to_trays_per_minute,
    sec_per_tray_to_velocity_rad_s,
)
from services.safety.sensor_service import (
    SafetyInterlockSnapshot,
    SafetySensorService,
    SafetySensorServiceConfig,
    SafetySensorStatusSnapshot,
)
from utils.config import config

logger = logging.getLogger(__name__)
_STATUS_REFRESH_INTERVAL_S = 0.25


class _MotorServiceProtocol(Protocol):
    def initialize(self) -> None: ...

    def start(self, initial_target_velocity_rad_s: float = 0.0) -> None: ...

    def stop(self) -> None: ...

    def shutdown(self) -> None: ...

    def rescan(self) -> bool: ...

    def set_target_velocity_rad_s(self, target_velocity_rad_s: float) -> float: ...

    def is_running(self) -> bool: ...

    def get_status_snapshots(self) -> list[MotorStatusSnapshot]: ...


class _SafetySensorServiceProtocol(Protocol):
    def initialize(self) -> None: ...

    def shutdown(self) -> None: ...

    def get_status_snapshots(self) -> list[SafetySensorStatusSnapshot]: ...

    def get_interlock_snapshot(self) -> SafetyInterlockSnapshot: ...


@ft.observable
class MotorController:
    def __init__(
        self,
        *,
        motor_service: _MotorServiceProtocol | None = None,
        safety_sensor_service: _SafetySensorServiceProtocol | None = None,
    ) -> None:
        self._lock = RLock()
        self.tray_size_cm = config.motor_tray_size_cm
        self.sec_per_tray_min = min(
            config.motor_min_sec_per_tray,
            config.motor_max_sec_per_tray,
        )
        self.sec_per_tray_max = max(
            config.motor_min_sec_per_tray,
            config.motor_max_sec_per_tray,
        )
        self.sec_per_tray = self._clamp_sec_per_tray(config.default_sec_per_tray)
        self.trays_per_minute = sec_per_tray_to_trays_per_minute(self.sec_per_tray)
        self.target_velocity_rad_s = 0.0
        self.is_motors_running = False
        self.status_refresh_enabled = False
        self.status_version = 0
        self.is_safety_interlock_enabled = config.safety_sensor_enabled
        self.is_safety_interlock_clear = not config.safety_sensor_enabled
        self.is_safety_interlock_blocked = False
        self.is_safety_interlock_faulted = False
        self.safety_interlock_reason = ""
        self._pending_safety_toast_message_key: str | None = None
        self._resume_after_safety_clear = False
        self._next_status_refresh_at_s = 0.0
        self._motor_service = motor_service or MotorService(
            MotorServiceConfig.from_app_config(config)
        )
        self._safety_sensor_service = safety_sensor_service or SafetySensorService(
            SafetySensorServiceConfig.from_app_config(config)
        )
        self.target_velocity_rad_s = self._resolve_target_velocity_rad_s()
        self._refresh_interlock_state(
            self._safety_sensor_service.get_interlock_snapshot()
        )

    def set_sec_per_tray(self, sec_per_tray: float) -> bool:
        with self._lock:
            normalized_sec_per_tray = self._clamp_sec_per_tray(sec_per_tray)
            if self.sec_per_tray == normalized_sec_per_tray:
                return False

            self.sec_per_tray = normalized_sec_per_tray
            self._apply_speed_to_motors()
            logger.info(
                "Tray time set to %.0fs/tray (target=%.3f rad/s)",
                self.sec_per_tray,
                self.target_velocity_rad_s,
            )
            return True

    def update_safety_and_motor_state(self) -> None:
        with self._lock:
            interlock = self._safety_sensor_service.get_interlock_snapshot()
            previous_blocked = self.is_safety_interlock_blocked
            previous_clear = self.is_safety_interlock_clear
            previous_reason = self.safety_interlock_reason

            self._refresh_interlock_state(interlock)

            if interlock.enabled and not interlock.is_clear:
                if self._motor_service.is_running():
                    self._resume_after_safety_clear = True
                    try:
                        self._motor_service.stop()
                        logger.warning(
                            "Safety interlock stop applied: %s", interlock.reason
                        )
                    except Exception:
                        logger.exception(
                            "Safety interlock failed to stop motors (%s)",
                            interlock.reason,
                        )
            elif (
                interlock.enabled
                and interlock.is_clear
                and self._resume_after_safety_clear
            ):
                try:
                    self._motor_service.start(
                        initial_target_velocity_rad_s=self.target_velocity_rad_s
                    )
                    self._resume_after_safety_clear = False
                    logger.info(
                        "Safety interlock cleared; motors resumed automatically"
                    )
                except Exception:
                    self._resume_after_safety_clear = False
                    logger.exception("Safety interlock clear could not restart motors")

            running = self._motor_service.is_running()
            if running != self.is_motors_running:
                self.is_motors_running = running
                logger.info("Motor running state changed to %s", self.is_motors_running)

            if interlock.enabled:
                if not previous_blocked and interlock.is_blocked:
                    self._pending_safety_toast_message_key = "safety_interlock_blocked"
                elif previous_blocked and interlock.is_clear:
                    self._pending_safety_toast_message_key = "safety_interlock_cleared"

                if previous_clear and not interlock.is_clear:
                    logger.warning("Safety interlock engaged: %s", interlock.reason)
                elif not previous_clear and interlock.is_clear:
                    logger.info("Safety interlock clear")
                elif previous_reason != interlock.reason and not interlock.is_clear:
                    logger.info("Safety interlock update: %s", interlock.reason)

            self._maybe_refresh_status_version()

    def set_status_refresh_enabled(self, enabled: bool) -> None:
        with self._lock:
            normalized_enabled = bool(enabled)
            if self.status_refresh_enabled == normalized_enabled:
                return

            self.status_refresh_enabled = normalized_enabled
            self._next_status_refresh_at_s = 0.0
            if normalized_enabled:
                self.status_version += 1

    def initialize_motors(self) -> None:
        with self._lock:
            try:
                self._safety_sensor_service.initialize()
            except Exception:
                logger.exception("Safety sensor initialization failed")

            try:
                self._motor_service.initialize()
            except Exception:
                logger.exception("Motor CAN initialization failed")

            self.update_safety_and_motor_state()

    def start_motors(self) -> MotorActionResult:
        with self._lock:
            interlock = self._safety_sensor_service.get_interlock_snapshot()
            self._refresh_interlock_state(interlock)
            if interlock.enabled and not interlock.is_clear:
                return MotorActionResult(
                    action=MotorAction.START_BLOCKED_BY_SAFETY,
                    error=interlock.reason,
                )

            try:
                self._motor_service.start(
                    initial_target_velocity_rad_s=self.target_velocity_rad_s
                )
                self._resume_after_safety_clear = False
                self.is_motors_running = self._motor_service.is_running()
                if self.is_motors_running:
                    return MotorActionResult(action=MotorAction.STARTED)

                return MotorActionResult(
                    action=MotorAction.START_FAILED,
                    error="Motor service did not enter running state",
                )
            except Exception as ex:
                self.is_motors_running = False
                logger.exception("Motor startup failed")
                if "No configured motors are connected" in str(ex):
                    return MotorActionResult(
                        action=MotorAction.START_FAILED_NO_MOTORS,
                        error=str(ex),
                    )
                return MotorActionResult(action=MotorAction.START_FAILED, error=str(ex))

    def stop_motors(self) -> MotorActionResult:
        with self._lock:
            try:
                self._resume_after_safety_clear = False
                self._motor_service.stop()
                self.is_motors_running = False
                return MotorActionResult(action=MotorAction.STOPPED)
            except Exception as ex:
                logger.exception("Motor shutdown failed")
                return MotorActionResult(action=MotorAction.STOP_FAILED, error=str(ex))

    def shutdown_motors(self) -> None:
        with self._lock:
            try:
                self._resume_after_safety_clear = False
                self._motor_service.shutdown()
                self.is_motors_running = False
            except Exception:
                logger.exception("Motor full shutdown failed")

            try:
                self._safety_sensor_service.shutdown()
            except Exception:
                logger.exception("Safety sensor shutdown failed")

    def rescan_motors(self) -> bool:
        with self._lock:
            try:
                running = self._motor_service.rescan()
                self.is_motors_running = running
                return True
            except Exception:
                logger.exception("Motor rescan failed")
                self.is_motors_running = self._motor_service.is_running()
                return False

    def toggle_motors(self) -> MotorActionResult:
        with self._lock:
            if self.is_motors_running:
                return self.stop_motors()
            return self.start_motors()

    def get_status_snapshots(self) -> list[MotorStatusSnapshot]:
        with self._lock:
            return self._motor_service.get_status_snapshots()

    def get_safety_sensor_snapshots(self) -> list[SafetySensorStatusSnapshot]:
        with self._lock:
            return self._safety_sensor_service.get_status_snapshots()

    def get_safety_interlock_snapshot(self) -> SafetyInterlockSnapshot:
        with self._lock:
            interlock = self._safety_sensor_service.get_interlock_snapshot()
            self._refresh_interlock_state(interlock)
            return interlock

    def consume_pending_safety_toast_message_key(self) -> str | None:
        with self._lock:
            message_key = self._pending_safety_toast_message_key
            self._pending_safety_toast_message_key = None
            return message_key

    def _apply_speed_to_motors(self) -> None:
        try:
            self.trays_per_minute = sec_per_tray_to_trays_per_minute(self.sec_per_tray)
            self.target_velocity_rad_s = self._resolve_target_velocity_rad_s()
            if self.is_motors_running:
                self.target_velocity_rad_s = (
                    self._motor_service.set_target_velocity_rad_s(
                        self.target_velocity_rad_s
                    )
                )
        except Exception:
            logger.exception("Failed to apply speed command to motors")

    def _clamp_sec_per_tray(self, sec_per_tray: float) -> float:
        return clamp_sec_per_tray(
            sec_per_tray,
            minimum=self.sec_per_tray_min,
            maximum=self.sec_per_tray_max,
        )

    def _resolve_target_velocity_rad_s(self) -> float:
        return sec_per_tray_to_velocity_rad_s(
            self.sec_per_tray,
            tray_size_cm=self.tray_size_cm,
        )

    def _refresh_interlock_state(self, interlock: SafetyInterlockSnapshot) -> None:
        self.is_safety_interlock_enabled = interlock.enabled
        self.is_safety_interlock_clear = interlock.is_clear
        self.is_safety_interlock_blocked = interlock.is_blocked
        self.is_safety_interlock_faulted = interlock.is_faulted
        self.safety_interlock_reason = interlock.reason

    def _maybe_refresh_status_version(self) -> None:
        if not self.status_refresh_enabled:
            return

        now_s = time.monotonic()
        if now_s < self._next_status_refresh_at_s:
            return

        self.status_version += 1
        self._next_status_refresh_at_s = now_s + _STATUS_REFRESH_INTERVAL_S
