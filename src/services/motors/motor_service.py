from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import RLock

from cubemars_servo_can import CubeMarsServoCAN

from utils.config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MotorServiceConfig:
    enabled: bool
    motor_type: str
    can_channel: str
    motor_1_id: int
    motor_2_id: int
    motor_1_direction: int
    motor_2_direction: int
    speed_min: int
    speed_max: int
    max_mosfet_temp_c: float

    @classmethod
    def from_app_config(cls, app_config: Config) -> "MotorServiceConfig":
        speed_min = app_config.motor_speed_min
        speed_max = app_config.motor_speed_max
        if speed_min > speed_max:
            speed_min, speed_max = speed_max, speed_min

        return cls(
            enabled=app_config.motor_enabled,
            motor_type=app_config.motor_type,
            can_channel=app_config.motor_can_channel,
            motor_1_id=app_config.motor_1_id,
            motor_2_id=app_config.motor_2_id,
            motor_1_direction=_normalize_direction(app_config.motor_1_direction),
            motor_2_direction=_normalize_direction(app_config.motor_2_direction),
            speed_min=speed_min,
            speed_max=speed_max,
            max_mosfet_temp_c=app_config.motor_max_temp_c,
        )

    @property
    def speed_domain(self) -> int:
        return max(abs(self.speed_min), abs(self.speed_max), 1)


def _normalize_direction(value: int) -> int:
    if value == 0:
        return 1
    return -1 if value < 0 else 1


class MotorService:
    def __init__(self, cfg: MotorServiceConfig) -> None:
        self._cfg = cfg
        self._lock = RLock()
        self._active = False
        self._motor_1: CubeMarsServoCAN | None = None
        self._motor_2: CubeMarsServoCAN | None = None
        self._max_motor_velocity_rad_s = 0.0

    def start(self, initial_speed_percent: int = 0) -> None:
        if not self._cfg.enabled:
            logger.info("Motor service disabled by config (MOTOR_ENABLED=false)")
            return

        with self._lock:
            if self._active:
                self.set_speed_percent(initial_speed_percent)
                return

            motor_1 = CubeMarsServoCAN(
                motor_type=self._cfg.motor_type,
                motor_ID=self._cfg.motor_1_id,
                max_mosfet_temp=self._cfg.max_mosfet_temp_c,
                can_channel=self._cfg.can_channel,
            )
            motor_2 = CubeMarsServoCAN(
                motor_type=self._cfg.motor_type,
                motor_ID=self._cfg.motor_2_id,
                max_mosfet_temp=self._cfg.max_mosfet_temp_c,
                can_channel=self._cfg.can_channel,
            )
            entered_1 = False
            entered_2 = False
            try:
                motor_1.__enter__()
                entered_1 = True
                motor_2.__enter__()
                entered_2 = True

                motor_1.enter_velocity_control()
                motor_2.enter_velocity_control()

                self._motor_1 = motor_1
                self._motor_2 = motor_2
                self._active = True
                self._max_motor_velocity_rad_s = min(
                    _motor_velocity_limit_rad_s(motor_1),
                    _motor_velocity_limit_rad_s(motor_2),
                )
                self._apply_speed_locked(initial_speed_percent)
                logger.info(
                    "Motor service started on %s with IDs [%s, %s]",
                    self._cfg.can_channel,
                    self._cfg.motor_1_id,
                    self._cfg.motor_2_id,
                )
            except Exception:
                if entered_2:
                    _safe_exit(motor_2)
                    _detach_motor_listener(motor_2)
                if entered_1:
                    _safe_exit(motor_1)
                    _detach_motor_listener(motor_1)
                _close_can_manager(motor_1)
                raise

    def stop(self) -> None:
        if not self._cfg.enabled:
            return

        with self._lock:
            if not self._active:
                return

            motor_1 = self._motor_1
            motor_2 = self._motor_2
            try:
                self._apply_speed_locked(0)
            except Exception:
                logger.exception("Failed to send zero-speed command during shutdown")
            finally:
                if motor_2 is not None:
                    _safe_exit(motor_2)
                    _detach_motor_listener(motor_2)
                if motor_1 is not None:
                    _safe_exit(motor_1)
                    _detach_motor_listener(motor_1)
                if motor_1 is not None:
                    _close_can_manager(motor_1)

                self._motor_1 = None
                self._motor_2 = None
                self._active = False
                self._max_motor_velocity_rad_s = 0.0
                logger.info("Motor service stopped")

    def set_speed_percent(self, speed_percent: int) -> int:
        if not self._cfg.enabled:
            return speed_percent

        with self._lock:
            if not self._active:
                logger.debug("Ignoring speed command while motor service is inactive")
                return self._clamp_speed(speed_percent)
            return self._apply_speed_locked(speed_percent)

    def _clamp_speed(self, speed_percent: int) -> int:
        return max(self._cfg.speed_min, min(speed_percent, self._cfg.speed_max))

    def _apply_speed_locked(self, speed_percent: int) -> int:
        motor_1 = self._motor_1
        motor_2 = self._motor_2
        if motor_1 is None or motor_2 is None:
            return self._clamp_speed(speed_percent)

        clamped_speed = self._clamp_speed(speed_percent)
        speed_ratio = float(clamped_speed) / float(self._cfg.speed_domain)
        base_velocity = speed_ratio * self._max_motor_velocity_rad_s

        motor_1.set_motor_velocity_radians_per_second(
            base_velocity * self._cfg.motor_1_direction
        )
        motor_2.set_motor_velocity_radians_per_second(
            base_velocity * self._cfg.motor_2_direction
        )
        motor_1.update()
        motor_2.update()
        return clamped_speed


def _safe_exit(motor: CubeMarsServoCAN) -> None:
    try:
        motor.__exit__(None, None, None)
    except Exception:
        logger.exception("Motor shutdown error")


def _detach_motor_listener(motor: CubeMarsServoCAN) -> None:
    try:
        motor._canman.remove_motor(motor)
    except Exception:
        logger.debug("Failed to detach motor listener for motor ID %s", motor.ID)


def _close_can_manager(motor: CubeMarsServoCAN) -> None:
    try:
        motor._canman.close()
    except Exception:
        logger.debug("Failed to close CAN manager")


def _motor_velocity_limit_rad_s(motor: CubeMarsServoCAN) -> float:
    return motor.config.V_max * motor.radps_per_ERPM * motor.config.GEAR_RATIO
