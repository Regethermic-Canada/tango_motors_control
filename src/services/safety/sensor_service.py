from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, RLock, Thread

from xkc_kl200_python import SensorConfig, XKC_KL200, XKC_KL200_Error

from utils.config import Config

logger = logging.getLogger(__name__)
_RECONNECT_INTERVAL_S = 0.5
_SETUP_RETRY_COUNT = 3


@dataclass(frozen=True)
class SafetySensorTarget:
    sensor_index: int
    label: str
    port: str
    stop_below_mm: int


@dataclass(frozen=True)
class SafetySensorServiceConfig:
    enabled: bool
    baudrate: int
    timeout_s: float
    startup_delay_s: float
    poll_interval_s: float
    upload_interval: int
    clear_confirmations: int
    stale_after_s: float
    targets: tuple[SafetySensorTarget, ...]

    @classmethod
    def from_app_config(cls, app_config: Config) -> "SafetySensorServiceConfig":
        poll_interval_s = max(0.01, app_config.safety_sensor_poll_interval_s)

        if not app_config.safety_sensor_enabled:
            return cls(
                enabled=False,
                baudrate=app_config.safety_sensor_baudrate,
                timeout_s=max(0.01, app_config.safety_sensor_timeout_s),
                startup_delay_s=max(0.0, app_config.safety_sensor_startup_delay_s),
                poll_interval_s=poll_interval_s,
                upload_interval=max(
                    1, min(100, app_config.safety_sensor_upload_interval)
                ),
                clear_confirmations=max(
                    1, app_config.safety_sensor_clear_confirmations
                ),
                stale_after_s=max(0.25, poll_interval_s * 5.0),
                targets=(),
            )

        ports = _dedupe_preserve_order(app_config.safety_sensor_ports)
        labels = list(app_config.safety_sensor_labels)
        thresholds = list(app_config.safety_sensor_stop_below_mm)

        if not ports:
            raise ValueError(
                "SAFETY_SENSOR_PORTS must contain at least one UART device when "
                "SAFETY_SENSOR_ENABLED=true"
            )

        if thresholds and len(thresholds) != len(ports):
            raise ValueError(
                "SAFETY_SENSOR_STOP_BELOW_MM must match SAFETY_SENSOR_PORTS count "
                f"(got {len(thresholds)} thresholds and {len(ports)} ports)"
            )

        if labels and len(labels) != len(ports):
            raise ValueError(
                "SAFETY_SENSOR_LABELS must match SAFETY_SENSOR_PORTS count "
                f"(got {len(labels)} labels and {len(ports)} ports)"
            )

        targets = tuple(
            SafetySensorTarget(
                sensor_index=index + 1,
                label=labels[index] if labels else f"Sensor {index + 1}",
                port=port,
                stop_below_mm=thresholds[index] if thresholds else 150,
            )
            for index, port in enumerate(ports)
        )

        for target in targets:
            if target.stop_below_mm <= 0:
                raise ValueError(
                    "SAFETY_SENSOR_STOP_BELOW_MM entries must be > 0 "
                    f"(invalid value {target.stop_below_mm} for {target.label})"
                )

        return cls(
            enabled=True,
            baudrate=app_config.safety_sensor_baudrate,
            timeout_s=max(0.01, app_config.safety_sensor_timeout_s),
            startup_delay_s=max(0.0, app_config.safety_sensor_startup_delay_s),
            poll_interval_s=poll_interval_s,
            upload_interval=max(1, min(100, app_config.safety_sensor_upload_interval)),
            clear_confirmations=max(1, app_config.safety_sensor_clear_confirmations),
            stale_after_s=max(0.25, poll_interval_s * 5.0),
            targets=targets,
        )


@dataclass(frozen=True)
class SafetySensorStatusSnapshot:
    sensor_index: int
    label: str
    port: str
    stop_below_mm: int
    distance_mm: int | None
    is_connected: bool
    is_ready: bool
    is_blocked: bool
    is_faulted: bool
    clear_read_streak: int
    age_s: float | None
    last_error: str | None


@dataclass(frozen=True)
class SafetyInterlockSnapshot:
    enabled: bool
    is_clear: bool
    is_blocked: bool
    is_faulted: bool
    is_waiting: bool
    reason: str
    blocked_labels: tuple[str, ...]
    faulted_labels: tuple[str, ...]
    waiting_labels: tuple[str, ...]


@dataclass
class _SensorRuntimeState:
    distance_mm: int | None = None
    is_connected: bool = False
    is_blocked: bool = False
    is_faulted: bool = False
    clear_read_streak: int = 0
    connected_since_monotonic_s: float | None = None
    last_update_monotonic_s: float | None = None
    last_error: str | None = None


@dataclass
class _ManagedSensor:
    target: SafetySensorTarget
    stop_event: Event
    thread: Thread | None = None


class SafetySensorService:
    def __init__(self, cfg: SafetySensorServiceConfig) -> None:
        self._cfg = cfg
        self._lock = RLock()
        self._initialized = False
        self._workers: list[_ManagedSensor] = []
        self._states = {
            target.sensor_index: _SensorRuntimeState() for target in self._cfg.targets
        }

    def initialize(self) -> None:
        if not self._cfg.enabled:
            logger.info(
                "Safety sensor service disabled by config (SAFETY_SENSOR_ENABLED=false)"
            )
            return

        with self._lock:
            if self._initialized:
                return

            workers: list[_ManagedSensor] = []
            for target in self._cfg.targets:
                stop_event = Event()
                thread = Thread(
                    target=self._sensor_loop,
                    name=f"safety-sensor-{target.sensor_index}",
                    args=(target, stop_event),
                    daemon=True,
                )
                workers.append(
                    _ManagedSensor(
                        target=target,
                        stop_event=stop_event,
                        thread=thread,
                    )
                )

            self._workers = workers
            self._initialized = True

        for worker in workers:
            if worker.thread is not None:
                worker.thread.start()

        logger.info(
            "Safety sensor service started for ports: %s",
            [target.port for target in self._cfg.targets],
        )

    def shutdown(self) -> None:
        with self._lock:
            workers = list(self._workers)
            self._workers = []
            self._initialized = False

        for worker in workers:
            worker.stop_event.set()

        for worker in workers:
            if worker.thread is not None:
                worker.thread.join(timeout=max(1.0, self._cfg.timeout_s * 2.0))

        with self._lock:
            for target in self._cfg.targets:
                self._states[target.sensor_index] = _SensorRuntimeState()

        if workers:
            logger.info("Safety sensor service shutdown complete")

    def get_status_snapshots(self) -> list[SafetySensorStatusSnapshot]:
        now_s = time.monotonic()
        snapshots: list[SafetySensorStatusSnapshot] = []

        with self._lock:
            for target in self._cfg.targets:
                state = self._states[target.sensor_index]
                freshness_reference_s = (
                    state.last_update_monotonic_s or state.connected_since_monotonic_s
                )
                age_s = (
                    None
                    if freshness_reference_s is None
                    else max(0.0, now_s - freshness_reference_s)
                )
                is_stale = (
                    freshness_reference_s is not None
                    and age_s is not None
                    and age_s > self._cfg.stale_after_s
                )
                is_faulted = state.is_faulted or is_stale
                is_ready = state.last_update_monotonic_s is not None and not is_faulted

                last_error: str | None
                if is_stale:
                    last_error = (
                        state.last_error
                        or f"No fresh measurement within {self._cfg.stale_after_s:.2f}s"
                    )
                else:
                    last_error = state.last_error

                snapshots.append(
                    SafetySensorStatusSnapshot(
                        sensor_index=target.sensor_index,
                        label=target.label,
                        port=target.port,
                        stop_below_mm=target.stop_below_mm,
                        distance_mm=state.distance_mm,
                        is_connected=state.is_connected,
                        is_ready=is_ready,
                        is_blocked=state.is_blocked and not is_faulted,
                        is_faulted=is_faulted,
                        clear_read_streak=state.clear_read_streak,
                        age_s=age_s,
                        last_error=last_error,
                    )
                )

        return snapshots

    def get_interlock_snapshot(self) -> SafetyInterlockSnapshot:
        if not self._cfg.enabled:
            return SafetyInterlockSnapshot(
                enabled=False,
                is_clear=True,
                is_blocked=False,
                is_faulted=False,
                is_waiting=False,
                reason="Safety interlock disabled",
                blocked_labels=(),
                faulted_labels=(),
                waiting_labels=(),
            )

        snapshots = self.get_status_snapshots()
        blocked_labels = tuple(
            snapshot.label for snapshot in snapshots if snapshot.is_blocked
        )
        faulted_labels = tuple(
            snapshot.label for snapshot in snapshots if snapshot.is_faulted
        )
        waiting_labels = tuple(
            snapshot.label
            for snapshot in snapshots
            if not snapshot.is_blocked
            and not snapshot.is_faulted
            and snapshot.clear_read_streak < self._cfg.clear_confirmations
        )
        is_clear = not blocked_labels and not faulted_labels and not waiting_labels
        is_blocked = bool(blocked_labels)
        is_faulted = bool(faulted_labels)
        is_waiting = bool(waiting_labels)

        if is_blocked:
            reason = f"Blocked by {', '.join(blocked_labels)}"
        elif is_faulted:
            reason = f"Faulted sensors: {', '.join(faulted_labels)}"
        elif is_waiting:
            reason = (
                "Waiting for stable clear readings from " f"{', '.join(waiting_labels)}"
            )
        else:
            reason = "All safety sensors are clear"

        return SafetyInterlockSnapshot(
            enabled=True,
            is_clear=is_clear,
            is_blocked=is_blocked,
            is_faulted=is_faulted,
            is_waiting=is_waiting,
            reason=reason,
            blocked_labels=blocked_labels,
            faulted_labels=faulted_labels,
            waiting_labels=waiting_labels,
        )

    def _sensor_loop(self, target: SafetySensorTarget, stop_event: Event) -> None:
        sensor: XKC_KL200 | None = None

        try:
            while not stop_event.is_set():
                if sensor is None:
                    try:
                        sensor = self._open_sensor(target)
                        self._set_connecting_state(target)
                    except Exception as ex:
                        self._set_fault_state(
                            target,
                            error=f"Setup failed: {ex}",
                            is_connected=False,
                        )
                        if stop_event.wait(_RECONNECT_INTERVAL_S):
                            return
                        continue

                try:
                    while sensor.process_auto_data():
                        distance_mm = sensor.get_last_received_distance()
                        self._set_measurement_state(target, distance_mm)

                    if self._is_sensor_stale(target):
                        self._set_fault_state(
                            target,
                            error=(
                                "Sensor data went stale "
                                f"after {self._cfg.stale_after_s:.2f}s"
                            ),
                            is_connected=False,
                        )
                        _safe_close_sensor(sensor)
                        sensor = None
                        if stop_event.wait(_RECONNECT_INTERVAL_S):
                            return
                        continue
                except Exception as ex:
                    self._set_fault_state(
                        target,
                        error=f"Read failed: {ex}",
                        is_connected=False,
                    )
                    _safe_close_sensor(sensor)
                    sensor = None
                    if stop_event.wait(_RECONNECT_INTERVAL_S):
                        return
                    continue

                if stop_event.wait(self._cfg.poll_interval_s):
                    return
        finally:
            _safe_close_sensor(sensor)
            self._set_disconnected_state(target)

    def _open_sensor(self, target: SafetySensorTarget) -> XKC_KL200:
        sensor = XKC_KL200(
            config=SensorConfig(
                port=target.port,
                baudrate=self._cfg.baudrate,
                timeout=self._cfg.timeout_s,
                startup_delay_s=self._cfg.startup_delay_s,
            )
        )

        self._configure_auto_upload(sensor)
        logger.info(
            "Safety sensor %s connected on %s (stop <= %s mm)",
            target.label,
            target.port,
            target.stop_below_mm,
        )
        return sensor

    def _configure_auto_upload(self, sensor: XKC_KL200) -> None:
        self._require_command_success(
            sensor,
            "set_upload_mode(False)",
            lambda: sensor.set_upload_mode(False),
        )
        self._require_command_success(
            sensor,
            f"set_upload_interval({self._cfg.upload_interval})",
            lambda: sensor.set_upload_interval(self._cfg.upload_interval),
        )
        self._require_command_success(
            sensor,
            "set_upload_mode(True)",
            lambda: sensor.set_upload_mode(True),
        )

    def _require_command_success(
        self,
        sensor: XKC_KL200,
        description: str,
        command: Callable[[], XKC_KL200_Error],
    ) -> None:
        last_error: XKC_KL200_Error | None = None
        for _ in range(_SETUP_RETRY_COUNT):
            _drain_sensor_input(sensor)
            result = command()
            if result == XKC_KL200_Error.SUCCESS:
                _drain_sensor_input(sensor)
                return
            last_error = result
            time.sleep(self._cfg.poll_interval_s)

        raise RuntimeError(f"{description} failed with {last_error!s}")

    def _set_connecting_state(self, target: SafetySensorTarget) -> None:
        now_s = time.monotonic()
        with self._lock:
            self._states[target.sensor_index] = _SensorRuntimeState(
                distance_mm=None,
                is_connected=True,
                is_blocked=False,
                is_faulted=False,
                clear_read_streak=0,
                connected_since_monotonic_s=now_s,
                last_update_monotonic_s=None,
                last_error=None,
            )

    def _set_measurement_state(
        self,
        target: SafetySensorTarget,
        distance_mm: int,
    ) -> None:
        now_s = time.monotonic()
        is_blocked = distance_mm <= target.stop_below_mm

        with self._lock:
            previous = self._states[target.sensor_index]
            clear_read_streak = 0 if is_blocked else previous.clear_read_streak + 1
            self._states[target.sensor_index] = _SensorRuntimeState(
                distance_mm=distance_mm,
                is_connected=True,
                is_blocked=is_blocked,
                is_faulted=False,
                clear_read_streak=clear_read_streak,
                connected_since_monotonic_s=previous.connected_since_monotonic_s,
                last_update_monotonic_s=now_s,
                last_error=None,
            )

    def _set_fault_state(
        self,
        target: SafetySensorTarget,
        *,
        error: str,
        is_connected: bool,
    ) -> None:
        with self._lock:
            previous = self._states[target.sensor_index]
            self._states[target.sensor_index] = _SensorRuntimeState(
                distance_mm=previous.distance_mm,
                is_connected=is_connected,
                is_blocked=False,
                is_faulted=True,
                clear_read_streak=0,
                connected_since_monotonic_s=previous.connected_since_monotonic_s,
                last_update_monotonic_s=previous.last_update_monotonic_s,
                last_error=error,
            )

        logger.warning("Safety sensor %s fault: %s", target.label, error)

    def _set_disconnected_state(self, target: SafetySensorTarget) -> None:
        with self._lock:
            previous = self._states[target.sensor_index]
            self._states[target.sensor_index] = _SensorRuntimeState(
                distance_mm=previous.distance_mm,
                is_connected=False,
                is_blocked=False,
                is_faulted=previous.is_faulted,
                clear_read_streak=0,
                connected_since_monotonic_s=previous.connected_since_monotonic_s,
                last_update_monotonic_s=previous.last_update_monotonic_s,
                last_error=previous.last_error,
            )

    def _is_sensor_stale(self, target: SafetySensorTarget) -> bool:
        now_s = time.monotonic()
        with self._lock:
            state = self._states[target.sensor_index]
            freshness_reference_s = (
                state.last_update_monotonic_s or state.connected_since_monotonic_s
            )
        if freshness_reference_s is None:
            return False
        return (now_s - freshness_reference_s) > self._cfg.stale_after_s


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized_value = value.strip()
        if not normalized_value or normalized_value in seen:
            continue
        unique_values.append(normalized_value)
        seen.add(normalized_value)
    return unique_values


def _drain_sensor_input(sensor: XKC_KL200) -> None:
    serial_manager = getattr(sensor, "_serial_manager", None)
    if serial_manager is None:
        return

    bytes_available = int(getattr(serial_manager, "bytes_available", 0))
    if bytes_available <= 0:
        return

    discard = getattr(serial_manager, "discard", None)
    if callable(discard):
        discard(bytes_available)


def _safe_close_sensor(sensor: XKC_KL200 | None) -> None:
    if sensor is None:
        return
    try:
        sensor.close()
    except Exception:
        logger.debug("Failed to close safety sensor cleanly", exc_info=True)
