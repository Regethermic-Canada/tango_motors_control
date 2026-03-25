import logging

import flet as ft

from models.motor_types import MotorAction, MotorActionResult
from services.motors.motor_service import (
    MotorService,
    MotorServiceConfig,
    MotorStatusSnapshot,
)
from utils.config import config

logger = logging.getLogger(__name__)


@ft.observable
class MotorController:
    def __init__(self) -> None:
        self.speed_max = abs(config.motor_max_step_speed)
        self.speed_min = -self.speed_max
        self.speed_level = self._clamp_speed(config.default_speed)
        self.speed_percent = 0
        self.speed_percent_max = min(100, abs(config.motor_max_speed))
        self.is_motors_running = False
        self._motors_armed = False
        self._motor_service = MotorService(MotorServiceConfig.from_app_config(config))
        self.speed_percent = self._level_to_percent(self.speed_level)

    def increment(self) -> bool:
        previous_speed = self.speed_level
        self.speed_level = self._clamp_speed(self.speed_level + 1)
        if self.speed_level == previous_speed:
            return False

        self._apply_speed_to_motors()
        logger.info(
            "Speed level incremented to %s (target=%s%%)",
            self.speed_level,
            self.speed_percent,
        )
        return True

    def decrement(self) -> bool:
        previous_speed = self.speed_level
        self.speed_level = self._clamp_speed(self.speed_level - 1)
        if self.speed_level == previous_speed:
            return False

        self._apply_speed_to_motors()
        logger.info(
            "Speed level decremented to %s (target=%s%%)",
            self.speed_level,
            self.speed_percent,
        )
        return True

    def can_increment(self) -> bool:
        return self.speed_level < max(self.speed_min, self.speed_max)

    def can_decrement(self) -> bool:
        return self.speed_level > min(self.speed_min, self.speed_max)

    def sync_motor_state(self) -> None:
        running = self._motor_service.is_running()
        if running != self.is_motors_running:
            self.is_motors_running = running
            logger.info("Motor running state changed to %s", self.is_motors_running)

    def initialize_motors(self) -> None:
        try:
            self._motor_service.initialize()
        except Exception:
            logger.exception("Motor CAN initialization failed")

    def start_motors(self) -> MotorActionResult:
        try:
            self._motor_service.start(initial_speed_percent=self.speed_percent)
            self.is_motors_running = self._motor_service.is_running()
            if self.is_motors_running:
                self._motors_armed = True
                return MotorActionResult(action=MotorAction.STARTED)

            self._motors_armed = False
            return MotorActionResult(
                action=MotorAction.START_FAILED,
                error="Motor service did not enter running state",
            )
        except Exception as ex:
            self.is_motors_running = False
            self._motors_armed = False
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
            self._motors_armed = False
            return MotorActionResult(action=MotorAction.STOPPED)
        except Exception as ex:
            logger.exception("Motor shutdown failed")
            return MotorActionResult(action=MotorAction.STOP_FAILED, error=str(ex))

    def shutdown_motors(self) -> None:
        try:
            self._motor_service.shutdown()
            self.is_motors_running = False
            self._motors_armed = False
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
            target_percent = self._level_to_percent(self.speed_level)

            if target_percent == 0:
                self.speed_percent = 0
                if self.is_motors_running:
                    self._motor_service.stop()
                    self.is_motors_running = False
                    logger.info("Speed reached 0%%; motors auto-stopped")
                return

            self.speed_percent = target_percent
            if not self.is_motors_running and self._motors_armed:
                self._motor_service.start(initial_speed_percent=target_percent)
                self.is_motors_running = self._motor_service.is_running()
                if self.is_motors_running:
                    logger.info(
                        "Speed left 0%% while armed; motors auto-started at %s%%",
                        target_percent,
                    )

            if self.is_motors_running:
                self.speed_percent = self._motor_service.set_speed_percent(
                    target_percent
                )
        except Exception:
            logger.exception("Failed to apply speed command to motors")

    def _clamp_speed(self, speed: int) -> int:
        low = min(self.speed_min, self.speed_max)
        high = max(self.speed_min, self.speed_max)
        return max(low, min(speed, high))

    def _level_to_percent(self, level: int) -> int:
        level = self._clamp_speed(level)
        if level == 0 or self.speed_max <= 0 or self.speed_percent_max <= 0:
            return 0

        return int(round((level / self.speed_max) * self.speed_percent_max))
