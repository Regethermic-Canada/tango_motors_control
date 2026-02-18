from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Event, RLock, Thread

from cubemars_servo_can import CubeMarsServoCAN

from utils.config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MotorServiceConfig:
    enabled: bool
    motor_type: str
    can_channel: str
    motor_ids: tuple[int, ...]
    motor_directions: tuple[int, ...]
    command_hz: float
    max_speed_percent: int
    max_mosfet_temp_c: float

    @classmethod
    def from_app_config(cls, app_config: Config) -> "MotorServiceConfig":
        # Keep ID order stable and drop duplicates.
        seen_ids: set[int] = set()
        ids: list[int] = []
        for motor_id in app_config.motor_ids:
            if motor_id not in seen_ids:
                ids.append(motor_id)
                seen_ids.add(motor_id)

        if not ids:
            raise ValueError("No motor IDs configured")

        directions = list(app_config.motor_directions)

        return cls(
            enabled=app_config.motor_enabled,
            motor_type=app_config.motor_type,
            can_channel=app_config.motor_can_channel,
            motor_ids=tuple(ids),
            motor_directions=tuple(directions),
            command_hz=max(1.0, app_config.motor_command_hz),
            max_speed_percent=min(100, max(0, abs(app_config.motor_max_speed))),
            max_mosfet_temp_c=app_config.motor_max_temp_c,
        )

    @property
    def motor_targets(self) -> list[tuple[int, int]]:
        if len(self.motor_ids) != len(self.motor_directions):
            raise ValueError(
                "MOTOR_IDS and MOTOR_DIRECTIONS must have the same number of entries "
                f"(got {len(self.motor_ids)} IDs and {len(self.motor_directions)} directions)"
            )

        if not self.motor_ids:
            raise ValueError("MOTOR_IDS must contain at least one motor ID")

        for idx, direction in enumerate(self.motor_directions):
            if direction not in (-1, 1):
                raise ValueError(
                    "MOTOR_DIRECTIONS entries must be -1 or 1 "
                    f"(invalid value {direction} at index {idx})"
                )

        return list(zip(self.motor_ids, self.motor_directions))


@dataclass
class _ManagedMotor:
    motor: CubeMarsServoCAN
    direction: int
    motor_id: int


class MotorService:
    def __init__(self, cfg: MotorServiceConfig) -> None:
        self._cfg = cfg
        self._lock = RLock()
        self._initialized = False
        self._active = False
        self._pool: list[_ManagedMotor] = []
        self._connected: list[_ManagedMotor] = []
        self._motors: list[_ManagedMotor] = []
        self._failed_start_ids: set[int] = set()
        self._max_motor_velocity_rad_s = 0.0
        self._target_speed_percent = 0
        self._keepalive_stop = Event()
        self._keepalive_thread: Thread | None = None

    def initialize(self) -> None:
        if not self._cfg.enabled:
            logger.info("Motor service disabled by config (MOTOR_ENABLED=false)")
            return

        with self._lock:
            self._ensure_initialized_locked()
            self._connect_available_locked()

    def start(self, initial_speed_percent: int = 0) -> None:
        if not self._cfg.enabled:
            logger.info("Motor service disabled by config (MOTOR_ENABLED=false)")
            return

        with self._lock:
            if self._active:
                self.set_speed_percent(initial_speed_percent)
                return

            self._ensure_initialized_locked()
            self._connect_available_locked()

            if not self._connected:
                raise RuntimeError("No configured motors are connected")

            self._motors = list(self._connected)
            self._active = True
            self._target_speed_percent = self._clamp_speed(initial_speed_percent)
            try:
                self._apply_speed_locked(self._target_speed_percent)
            except Exception:
                logger.exception(
                    "Initial motor command failed; attempting full auto-reconnect"
                )
                self._reconnect_all_runtime_locked()
            self._start_keepalive_loop_locked()
            logger.info(
                "Motor service started on %s with active IDs: %s",
                self._cfg.can_channel,
                [item.motor_id for item in self._motors],
            )

    def stop(self) -> None:
        if not self._cfg.enabled:
            return

        keepalive_thread: Thread | None = None
        with self._lock:
            if not self._active:
                return
            self._target_speed_percent = 0
            keepalive_thread = self._signal_keepalive_stop_locked()

        if keepalive_thread is not None:
            keepalive_thread.join(timeout=1.0)

        with self._lock:
            if not self._active:
                return
            motors = list(self._motors)
            # Rely on library shutdown semantics (__exit__ sends 0.0A).
            for item in motors:
                _safe_exit(item.motor)

            self._motors = []
            self._connected = []
            self._active = False
            self._max_motor_velocity_rad_s = 0.0
            self._target_speed_percent = 0
            self._keepalive_thread = None
            self._keepalive_stop = Event()
            logger.info("Motor service stopped")

    def shutdown(self) -> None:
        if not self._cfg.enabled:
            return

        self.stop()
        with self._lock:
            self._reset_connection_locked()
            logger.info("Motor service shutdown complete")

    def rescan(self) -> bool:
        if not self._cfg.enabled:
            return False

        target_speed_percent = 0
        was_running = False
        with self._lock:
            was_running = self._active
            target_speed_percent = self._target_speed_percent

        self.shutdown()
        self.initialize()

        if was_running:
            self.start(initial_speed_percent=target_speed_percent)
        return self.is_running()

    def set_speed_percent(self, speed_percent: int) -> int:
        if not self._cfg.enabled:
            return speed_percent

        with self._lock:
            clamped_speed = self._clamp_speed(speed_percent)
            self._target_speed_percent = clamped_speed
            if not self._active:
                logger.debug("Speed updated while motor service inactive")
                return clamped_speed
            try:
                return self._apply_speed_locked(clamped_speed)
            except Exception:
                logger.exception("Speed command failed; attempting full auto-reconnect")
                self._reconnect_all_runtime_locked()
                return self._target_speed_percent

    def _clamp_speed(self, speed_percent: int) -> int:
        return max(
            -self._cfg.max_speed_percent,
            min(speed_percent, self._cfg.max_speed_percent),
        )

    def _apply_speed_locked(self, speed_percent: int) -> int:
        if not self._motors:
            return self._clamp_speed(speed_percent)

        clamped_speed = self._clamp_speed(speed_percent)
        speed_ratio = float(clamped_speed) / 100.0
        base_velocity = speed_ratio * self._max_motor_velocity_rad_s

        failed: list[_ManagedMotor] = []
        for item in self._motors:
            try:
                item.motor.set_motor_velocity_radians_per_second(
                    base_velocity * item.direction
                )
                item.motor.update()
            except Exception:
                logger.warning(
                    "Motor ID %s command failed, removing from active set",
                    item.motor_id,
                    exc_info=True,
                )
                failed.append(item)

        if failed:
            failed_ids = [item.motor_id for item in failed]
            raise RuntimeError(
                "Motor command failure on IDs "
                f"{failed_ids}; full shutdown and auto-reconnect required"
            )

        return clamped_speed

    def is_running(self) -> bool:
        return self._active

    def _start_keepalive_loop_locked(self) -> None:
        self._keepalive_stop = Event()
        self._keepalive_thread = Thread(
            target=self._keepalive_loop,
            name="motor-keepalive",
            daemon=True,
        )
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        period_s = 1.0 / max(1.0, self._cfg.command_hz)
        while not self._keepalive_stop.wait(period_s):
            with self._lock:
                if not self._active:
                    return
                try:
                    self._apply_speed_locked(self._target_speed_percent)
                except Exception:
                    logger.exception(
                        "Motor keepalive command failed; attempting full auto-reconnect"
                    )
                    try:
                        self._reconnect_all_runtime_locked()
                    except Exception:
                        logger.exception("Auto-reconnect failed; motor service stopped")
                        self._active = False
                        return

    def _build_pool_locked(self) -> None:
        pool: list[_ManagedMotor] = []
        for motor_id, direction in self._cfg.motor_targets:
            motor = CubeMarsServoCAN(
                motor_type=self._cfg.motor_type,
                motor_ID=motor_id,
                max_mosfet_temp=self._cfg.max_mosfet_temp_c,
                can_channel=self._cfg.can_channel,
            )
            pool.append(
                _ManagedMotor(
                    motor=motor,
                    direction=direction,
                    motor_id=motor_id,
                )
            )

        self._pool = pool
        self._connected = []
        self._failed_start_ids.clear()
        self._initialized = True
        logger.info(
            "Motor CAN interface initialized on %s for IDs: %s",
            self._cfg.can_channel,
            [item.motor_id for item in self._pool],
        )

    def _connect_available_locked(self) -> None:
        connected_by_id = {item.motor_id for item in self._connected}
        new_connected: list[int] = []
        for item in self._pool:
            if item.motor_id in connected_by_id:
                continue
            if item.motor_id in self._failed_start_ids:
                continue

            entered = False
            try:
                item.motor.__enter__()
                entered = True
                item.motor.enter_velocity_control()
                # Prime one safe zero-speed update so first Start has no connection/setup latency.
                item.motor.set_motor_velocity_radians_per_second(0.0)
                item.motor.update()
                self._connected.append(item)
                new_connected.append(item.motor_id)
            except Exception:
                logger.warning(
                    "Skipping unavailable motor ID %s on %s",
                    item.motor_id,
                    self._cfg.can_channel,
                )
                self._failed_start_ids.add(item.motor_id)
                if entered:
                    _safe_exit(item.motor)

        if self._connected:
            self._max_motor_velocity_rad_s = min(
                _motor_velocity_limit_rad_s(item.motor) for item in self._connected
            )
        else:
            self._max_motor_velocity_rad_s = 0.0

        if new_connected:
            logger.info(
                "Motor pre-connection ready on %s for IDs: %s",
                self._cfg.can_channel,
                new_connected,
            )

    def _reconnect_all_runtime_locked(self) -> None:
        target_speed_percent = self._clamp_speed(self._target_speed_percent)
        self._teardown_all_motors_locked()
        self._build_pool_locked()
        self._connect_available_locked()

        if not self._connected:
            self._active = False
            self._motors = []
            self._target_speed_percent = 0
            raise RuntimeError(
                "Automatic reconnect failed: no configured motors are connected"
            )

        self._motors = list(self._connected)
        self._active = True
        self._target_speed_percent = target_speed_percent
        self._apply_speed_locked(self._target_speed_percent)
        logger.info(
            "Motor service auto-reconnected on %s with active IDs: %s",
            self._cfg.can_channel,
            [item.motor_id for item in self._motors],
        )

    def _ensure_initialized_locked(self) -> None:
        if self._initialized:
            return
        self._build_pool_locked()

    def _signal_keepalive_stop_locked(self) -> Thread | None:
        keepalive_thread = self._keepalive_thread
        if keepalive_thread is not None:
            self._keepalive_stop.set()
        return keepalive_thread

    def _reset_connection_locked(self) -> None:
        self._signal_keepalive_stop_locked()
        self._active = False
        self._teardown_all_motors_locked()
        self._keepalive_thread = None
        self._keepalive_stop = Event()

    def _teardown_all_motors_locked(self) -> None:
        by_id: dict[int, _ManagedMotor] = {}
        for item in self._connected:
            by_id[item.motor_id] = item
        for item in self._motors:
            by_id[item.motor_id] = item
        for item in self._pool:
            by_id[item.motor_id] = item

        managed = list(by_id.values())
        for item in managed:
            _safe_exit(item.motor)
        for item in managed:
            _detach_motor_listener(item.motor)
        if managed:
            _close_can_manager(managed[0].motor)

        self._motors = []
        self._pool = []
        self._connected = []
        self._failed_start_ids.clear()
        self._initialized = False
        self._max_motor_velocity_rad_s = 0.0
        self._target_speed_percent = 0


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
