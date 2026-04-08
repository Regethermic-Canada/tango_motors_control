import logging

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
from utils.config import config

logger = logging.getLogger(__name__)


@ft.observable
class MotorController:
    def __init__(self) -> None:
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
        self._motor_service = MotorService(MotorServiceConfig.from_app_config(config))
        self.target_velocity_rad_s = self._resolve_target_velocity_rad_s()

    def set_sec_per_tray(self, sec_per_tray: float) -> bool:
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

    def sync_motor_state(self) -> None:
        running = self._motor_service.is_running()
        if running != self.is_motors_running:
            self.is_motors_running = running
            logger.info("Motor running state changed to %s", self.is_motors_running)
        if self.status_refresh_enabled:
            self.status_version += 1

    def set_status_refresh_enabled(self, enabled: bool) -> None:
        normalized_enabled = bool(enabled)
        if self.status_refresh_enabled == normalized_enabled:
            return

        self.status_refresh_enabled = normalized_enabled
        if normalized_enabled:
            self.status_version += 1

    def initialize_motors(self) -> None:
        try:
            self._motor_service.initialize()
        except Exception:
            logger.exception("Motor CAN initialization failed")

    def start_motors(self) -> MotorActionResult:
        try:
            self._motor_service.start(
                initial_target_velocity_rad_s=self.target_velocity_rad_s
            )
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
        try:
            self._motor_service.stop()
            self.is_motors_running = False
            return MotorActionResult(action=MotorAction.STOPPED)
        except Exception as ex:
            logger.exception("Motor shutdown failed")
            return MotorActionResult(action=MotorAction.STOP_FAILED, error=str(ex))

    def shutdown_motors(self) -> None:
        try:
            self._motor_service.shutdown()
            self.is_motors_running = False
        except Exception:
            logger.exception("Motor full shutdown failed")

    def rescan_motors(self) -> bool:
        try:
            running = self._motor_service.rescan()
            self.is_motors_running = running
            return True
        except Exception:
            logger.exception("Motor rescan failed")
            self.is_motors_running = self._motor_service.is_running()
            return False

    def toggle_motors(self) -> MotorActionResult:
        if self.is_motors_running:
            return self.stop_motors()
        return self.start_motors()

    def get_status_snapshots(self) -> list[MotorStatusSnapshot]:
        return self._motor_service.get_status_snapshots()

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
