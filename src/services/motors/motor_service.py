from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Event, RLock, Thread

from cubemars_servo_can import CubeMarsServoCAN

from .speed_ramp import SpeedRamp
from .tray_speed import sec_per_tray_to_velocity_rad_s
from utils.config import Config

logger = logging.getLogger(__name__)
_TEMP_MONITOR_INTERVAL_S = 1.0


@dataclass(frozen=True)
class MotorServiceConfig:
    enabled: bool
    motor_type: str
    can_channel: str
    motor_ids: tuple[int, ...]
    motor_directions: tuple[int, ...]
    command_hz: float
    ramp_time_s: float
    hold_release_timeout_s: float
    max_target_velocity_rad_s: float
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
            ramp_time_s=max(0.0, app_config.motor_ramp_time_s),
            hold_release_timeout_s=max(0.0, app_config.motor_hold_release_timeout_s),
            max_target_velocity_rad_s=sec_per_tray_to_velocity_rad_s(
                min(
                    app_config.motor_min_sec_per_tray,
                    app_config.motor_max_sec_per_tray,
                ),
                tray_size_cm=app_config.motor_tray_size_cm,
            ),
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


@dataclass(frozen=True)
class MotorStatusSnapshot:
    motor_id: int
    direction: int
    is_connected: bool
    is_running: bool
    temperature_c: float | None
    output_velocity_rad_s: float | None
    output_torque_nm: float | None
    qaxis_current_a: float | None


class _ServiceState(Enum):
    OFF = "off"
    HOLDING = "holding"
    RUNNING = "running"


class MotorService:
    def __init__(self, cfg: MotorServiceConfig) -> None:
        self._cfg = cfg
        self._lock = RLock()
        self._initialized = False
        self._state = _ServiceState.OFF
        self._pool: list[_ManagedMotor] = []
        self._connected: list[_ManagedMotor] = []
        self._motors: list[_ManagedMotor] = []
        self._failed_start_ids: set[int] = set()
        self._max_motor_velocity_rad_s = 0.0
        self._speed_ramp = SpeedRamp(
            max_command_value=self._cfg.max_target_velocity_rad_s,
            command_hz=self._cfg.command_hz,
            ramp_time_s=self._cfg.ramp_time_s,
        )
        self._keepalive_stop = Event()
        self._keepalive_thread: Thread | None = None
        self._next_temp_log_at_s = 0.0
        self._holding_since_s: float | None = None

    def initialize(self) -> None:
        if not self._cfg.enabled:
            logger.info("Motor service disabled by config (MOTOR_ENABLED=false)")
            return

        with self._lock:
            self._ensure_initialized_locked()
            self._connect_available_locked()

    def start(self, initial_target_velocity_rad_s: float = 0.0) -> None:
        if not self._cfg.enabled:
            logger.info("Motor service disabled by config (MOTOR_ENABLED=false)")
            return

        with self._lock:
            if self._is_service_active_locked():
                self._state = _ServiceState.RUNNING
                self._holding_since_s = None
                self._speed_ramp.set_target(
                    self._clamp_target_velocity_locked(initial_target_velocity_rad_s)
                )
                try:
                    self._drive_toward_target_locked()
                except Exception:
                    logger.exception(
                        "Speed command failed; attempting full auto-reconnect"
                    )
                    self._reconnect_all_runtime_locked()
                return

            self._ensure_initialized_locked()
            self._connect_available_locked()

            if not self._connected:
                raise RuntimeError("No configured motors are connected")

            self._motors = list(self._connected)
            self._state = _ServiceState.RUNNING
            self._next_temp_log_at_s = 0.0
            self._holding_since_s = None
            self._speed_ramp.reset()
            self._speed_ramp.set_target(
                self._clamp_target_velocity_locked(initial_target_velocity_rad_s)
            )
            try:
                applied_velocity = self._send_speed_command_locked(
                    self._speed_ramp.commanded_command_value
                )
                self._speed_ramp.set_commanded(applied_velocity)
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

        with self._lock:
            if not self._is_service_active_locked() and not self._motors:
                return
            self._state = _ServiceState.HOLDING
            self._holding_since_s = None
            self._speed_ramp.set_target(0)
            timeout_s = self._speed_ramp.stop_timeout_s()

        if not self._wait_until_commanded_zero(timeout_s):
            logger.warning(
                "Timed out waiting for motor ramp-down after %.2fs; forcing final zero command",
                timeout_s,
            )

        with self._lock:
            if not self._is_service_active_locked() or not self._motors:
                return
            try:
                self._send_speed_command_locked(0.0)
                self._speed_ramp.set_target(0)
                self._speed_ramp.set_commanded(0.0)
                self._holding_since_s = time.monotonic()
            except Exception:
                logger.exception("Final zero-speed command failed during stop")

            logger.info(
                "Motor service stopped (holding 0 rad/s; auto-release in %.1fs)",
                self._cfg.hold_release_timeout_s,
            )

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

        was_running = False
        with self._lock:
            was_running = self._state is _ServiceState.RUNNING
            target_velocity_rad_s = self._speed_ramp.target_command_value

        self.shutdown()
        self.initialize()

        if was_running:
            self.start(initial_target_velocity_rad_s=target_velocity_rad_s)
        return self.is_running()

    def set_target_velocity_rad_s(self, target_velocity_rad_s: float) -> float:
        if not self._cfg.enabled:
            return target_velocity_rad_s

        with self._lock:
            clamped_velocity = self._speed_ramp.set_target(
                self._clamp_target_velocity_locked(target_velocity_rad_s)
            )
            if not self._is_service_active_locked():
                logger.debug("Speed updated while motor service inactive")
                return clamped_velocity
            try:
                self._drive_toward_target_locked()
                return self._speed_ramp.commanded_command_value
            except Exception:
                logger.exception("Speed command failed; attempting full auto-reconnect")
                self._reconnect_all_runtime_locked()
                return self._speed_ramp.target_command_value

    def get_status_snapshots(self) -> list[MotorStatusSnapshot]:
        with self._lock:
            self._refresh_connections_for_status_locked()
            pool_by_id = {item.motor_id: item for item in self._pool}
            connected_by_id = {item.motor_id: item for item in self._connected}
            active_by_id = {item.motor_id: item for item in self._motors}

            snapshots: list[MotorStatusSnapshot] = []
            for motor_id, direction in self._cfg.motor_targets:
                managed = (
                    active_by_id.get(motor_id)
                    or connected_by_id.get(motor_id)
                    or pool_by_id.get(motor_id)
                )
                is_connected = motor_id in connected_by_id
                is_running = (
                    self._state is _ServiceState.RUNNING and motor_id in active_by_id
                )
                motor = managed.motor if is_connected and managed is not None else None
                snapshots.append(
                    MotorStatusSnapshot(
                        motor_id=motor_id,
                        direction=direction,
                        is_connected=is_connected,
                        is_running=is_running,
                        temperature_c=_safe_metric_read(
                            motor,
                            lambda item: item.get_temperature_celsius(),
                        ),
                        output_velocity_rad_s=_safe_metric_read(
                            motor,
                            lambda item: item.get_output_velocity_radians_per_second(),
                        ),
                        output_torque_nm=_safe_metric_read(
                            motor,
                            lambda item: item.get_output_torque_newton_meters(),
                        ),
                        qaxis_current_a=_safe_metric_read(
                            motor,
                            lambda item: item.get_current_qaxis_amps(),
                        ),
                    )
                )
            return snapshots

    def _refresh_connections_for_status_locked(self) -> None:
        if not self._cfg.enabled:
            return
        if self._state is _ServiceState.RUNNING:
            return

        self._ensure_initialized_locked()
        self._connect_available_locked()

    def _send_speed_command_locked(self, velocity_rad_s: float) -> float:
        clamped_velocity = self._clamp_target_velocity_locked(velocity_rad_s)
        if not self._motors:
            return clamped_velocity

        failed: list[_ManagedMotor] = []
        for item in self._motors:
            try:
                item.motor.set_output_velocity_radians_per_second(
                    clamped_velocity * item.direction
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

        return clamped_velocity

    def is_running(self) -> bool:
        return self._state is _ServiceState.RUNNING

    def _start_keepalive_loop_locked(self) -> None:
        self._keepalive_stop = Event()
        self._keepalive_thread = Thread(
            target=self._keepalive_loop,
            name="motor-keepalive",
            daemon=True,
        )
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        period_s = self._speed_ramp.command_period_s()
        while True:
            now_s = time.monotonic()
            with self._lock:
                if not self._is_service_active_locked():
                    return
                try:
                    self._drive_toward_target_locked()
                    self._maybe_log_motor_temperatures_locked(now_s)
                    if self._maybe_auto_release_hold_locked(now_s):
                        return
                except Exception:
                    logger.exception(
                        "Motor keepalive command failed; attempting full auto-reconnect"
                    )
                    try:
                        self._reconnect_all_runtime_locked()
                    except Exception:
                        logger.exception("Auto-reconnect failed; motor service stopped")
                        self._state = _ServiceState.OFF
                        return
            if self._keepalive_stop.wait(period_s):
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
        previous_state = self._state
        target_velocity_rad_s = self._speed_ramp.target_command_value
        commanded_velocity_rad_s = self._speed_ramp.commanded_command_value
        self._teardown_all_motors_locked()
        self._build_pool_locked()
        self._connect_available_locked()

        if not self._connected:
            self._state = _ServiceState.OFF
            self._motors = []
            raise RuntimeError(
                "Automatic reconnect failed: no configured motors are connected"
            )

        self._motors = list(self._connected)
        self._state = previous_state
        self._next_temp_log_at_s = 0.0
        self._holding_since_s = (
            time.monotonic() if previous_state is _ServiceState.HOLDING else None
        )
        self._speed_ramp.set_target(target_velocity_rad_s)
        self._speed_ramp.set_commanded(commanded_velocity_rad_s)
        applied_velocity = self._send_speed_command_locked(
            self._speed_ramp.commanded_command_value
        )
        self._speed_ramp.set_commanded(applied_velocity)
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
        self._state = _ServiceState.OFF
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
        self._next_temp_log_at_s = 0.0
        self._holding_since_s = None
        self._speed_ramp.reset()

    def _drive_toward_target_locked(self) -> None:
        next_velocity = self._speed_ramp.next_command_value()
        applied_velocity = self._send_speed_command_locked(next_velocity)
        self._speed_ramp.set_commanded(applied_velocity)

    def _clamp_target_velocity_locked(self, velocity_rad_s: float) -> float:
        clamped_velocity = self._speed_ramp.clamp_float(velocity_rad_s)
        if self._max_motor_velocity_rad_s <= 0.0:
            return clamped_velocity

        velocity_limit = min(
            self._cfg.max_target_velocity_rad_s,
            self._max_motor_velocity_rad_s,
        )
        return max(-velocity_limit, min(clamped_velocity, velocity_limit))

    def _wait_until_commanded_zero(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        period_s = self._speed_ramp.command_period_s()
        while time.monotonic() < deadline:
            with self._lock:
                if not self._is_service_active_locked() or not self._motors:
                    return True
                if self._speed_ramp.is_commanded_zero():
                    return True
            time.sleep(period_s)
        return False

    def _maybe_log_motor_temperatures_locked(self, now_s: float) -> None:
        if not logger.isEnabledFor(logging.INFO):
            return
        if not self._motors:
            return
        if now_s < self._next_temp_log_at_s:
            return

        temperature_samples = ", ".join(
            f"{item.motor_id}={item.motor.get_temperature_celsius():.1f}C"
            for item in self._motors
        )
        logger.info("Motor temperatures: %s", temperature_samples)
        self._next_temp_log_at_s = now_s + _TEMP_MONITOR_INTERVAL_S

    def _maybe_auto_release_hold_locked(self, now_s: float) -> bool:
        if self._state is not _ServiceState.HOLDING:
            return False
        if self._holding_since_s is None:
            return False
        if (now_s - self._holding_since_s) < self._cfg.hold_release_timeout_s:
            return False

        logger.info(
            "Motor hold timeout reached (%.1fs); releasing motors",
            self._cfg.hold_release_timeout_s,
        )
        self._release_all_motors_locked()
        return True

    def _release_all_motors_locked(self) -> None:
        self._state = _ServiceState.OFF
        self._teardown_all_motors_locked()
        self._keepalive_thread = None
        self._keepalive_stop = Event()

    def _is_service_active_locked(self) -> bool:
        return self._state is not _ServiceState.OFF


def _safe_exit(motor: CubeMarsServoCAN) -> None:
    try:
        motor.close()
    except Exception:
        logger.exception("Motor shutdown error")


def _safe_metric_read(
    motor: CubeMarsServoCAN | None,
    reader: Callable[[CubeMarsServoCAN], float],
) -> float | None:
    if motor is None:
        return None
    try:
        return float(reader(motor))
    except Exception:
        return None


def _detach_motor_listener(motor: CubeMarsServoCAN) -> None:
    try:
        motor.detach_listener()
    except Exception:
        logger.debug("Failed to detach motor listener for motor ID %s", motor.ID)


def _close_can_manager(motor: CubeMarsServoCAN) -> None:
    try:
        motor.close_shared_can_manager()
    except Exception:
        logger.debug("Failed to close CAN manager")


def _motor_velocity_limit_rad_s(motor: CubeMarsServoCAN) -> float:
    return motor.config.V_max * motor.radps_per_ERPM
