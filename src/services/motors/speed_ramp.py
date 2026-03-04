from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SpeedRamp:
    max_speed_percent: int
    command_hz: float
    ramp_time_s: float
    _target_speed_percent: int = field(init=False, default=0)
    _commanded_speed_percent: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.max_speed_percent = max(0, abs(self.max_speed_percent))
        self.command_hz = max(1.0, self.command_hz)
        self.ramp_time_s = max(0.0, self.ramp_time_s)

    @property
    def target_speed_percent(self) -> int:
        return self._target_speed_percent

    @property
    def commanded_speed_percent(self) -> float:
        return self._commanded_speed_percent

    def clamp(self, speed_percent: int) -> int:
        return max(
            -self.max_speed_percent,
            min(speed_percent, self.max_speed_percent),
        )

    def clamp_float(self, speed_percent: float) -> float:
        max_speed = float(self.max_speed_percent)
        return max(-max_speed, min(float(speed_percent), max_speed))

    def set_target(self, speed_percent: int) -> int:
        clamped_speed = self.clamp(speed_percent)
        self._target_speed_percent = clamped_speed
        return clamped_speed

    def set_commanded(self, speed_percent: float) -> float:
        clamped_speed = self.clamp_float(speed_percent)
        self._commanded_speed_percent = clamped_speed
        return clamped_speed

    def reset(self) -> None:
        self._target_speed_percent = 0
        self._commanded_speed_percent = 0.0

    def command_period_s(self) -> float:
        return 1.0 / self.command_hz

    def next_commanded_speed(self) -> float:
        target_speed = float(self._target_speed_percent)
        delta = target_speed - self._commanded_speed_percent
        if abs(delta) <= 1e-9 or self.ramp_time_s <= 0.0:
            return target_speed

        step_limit = self._step_percent()
        if abs(delta) <= step_limit:
            return target_speed
        if delta > 0.0:
            return self._commanded_speed_percent + step_limit
        return self._commanded_speed_percent - step_limit

    def is_commanded_zero(self) -> bool:
        return abs(self._commanded_speed_percent) <= 1e-9

    def stop_timeout_s(self) -> float:
        if self.max_speed_percent <= 0:
            return self.command_period_s()

        speed_fraction = min(
            1.0,
            abs(self._commanded_speed_percent) / float(self.max_speed_percent),
        )
        expected_ramp = speed_fraction * self.ramp_time_s
        return max(
            self.command_period_s(),
            expected_ramp + (2.0 * self.command_period_s()),
        )

    def _step_percent(self) -> float:
        if self.max_speed_percent <= 0:
            return 0.0
        return (
            float(self.max_speed_percent) * self.command_period_s()
        ) / self.ramp_time_s
