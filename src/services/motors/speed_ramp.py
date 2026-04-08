from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SpeedRamp:
    max_command_value: float
    command_hz: float
    ramp_time_s: float
    _target_command_value: float = field(init=False, default=0.0)
    _commanded_command_value: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.max_command_value = max(0.0, abs(self.max_command_value))
        self.command_hz = max(1.0, self.command_hz)
        self.ramp_time_s = max(0.0, self.ramp_time_s)

    @property
    def target_command_value(self) -> float:
        return self._target_command_value

    @property
    def commanded_command_value(self) -> float:
        return self._commanded_command_value

    def clamp_float(self, command_value: float) -> float:
        return max(
            -self.max_command_value,
            min(float(command_value), self.max_command_value),
        )

    def set_target(self, command_value: float) -> float:
        clamped_command = self.clamp_float(command_value)
        self._target_command_value = clamped_command
        return clamped_command

    def set_commanded(self, command_value: float) -> float:
        clamped_command = self.clamp_float(command_value)
        self._commanded_command_value = clamped_command
        return clamped_command

    def reset(self) -> None:
        self._target_command_value = 0.0
        self._commanded_command_value = 0.0

    def command_period_s(self) -> float:
        return 1.0 / self.command_hz

    def next_command_value(self) -> float:
        delta = self._target_command_value - self._commanded_command_value
        if abs(delta) <= 1e-9 or self.ramp_time_s <= 0.0:
            return self._target_command_value

        step_limit = self._step_value()
        if abs(delta) <= step_limit:
            return self._target_command_value
        if delta > 0.0:
            return self._commanded_command_value + step_limit
        return self._commanded_command_value - step_limit

    def is_commanded_zero(self) -> bool:
        return abs(self._commanded_command_value) <= 1e-9

    def stop_timeout_s(self) -> float:
        if self.max_command_value <= 0:
            return self.command_period_s()

        speed_fraction = min(
            1.0,
            abs(self._commanded_command_value) / self.max_command_value,
        )
        expected_ramp = speed_fraction * self.ramp_time_s
        return max(
            self.command_period_s(),
            expected_ramp + (2.0 * self.command_period_s()),
        )

    def _step_value(self) -> float:
        if self.max_command_value <= 0:
            return 0.0
        return (self.max_command_value * self.command_period_s()) / self.ramp_time_s
