from __future__ import annotations

_MIN_TRAY_SIZE_CM = 0.1
_EPSILON = 1e-9


def clamp_sec_per_tray(
    sec_per_tray: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    low = min(minimum, maximum)
    high = max(minimum, maximum)
    return max(low, min(float(sec_per_tray), high))


def sec_per_tray_to_trays_per_second(sec_per_tray: float) -> float:
    safe_sec_per_tray = max(float(sec_per_tray), _EPSILON)
    return 1.0 / safe_sec_per_tray


def sec_per_tray_to_trays_per_minute(sec_per_tray: float) -> float:
    return sec_per_tray_to_trays_per_second(sec_per_tray) * 60.0


def trays_per_minute_to_sec_per_tray(trays_per_minute: float) -> float:
    safe_trays_per_minute = max(float(trays_per_minute), _EPSILON)
    return 60.0 / safe_trays_per_minute


def sec_per_tray_to_velocity_rad_s(
    sec_per_tray: float,
    *,
    tray_size_cm: float,
) -> float:
    # The tray-time target is treated as tangential travel of one tray length
    # across a tray with the configured diameter.
    safe_sec_per_tray = max(float(sec_per_tray), _EPSILON)
    tray_size_m = max(float(tray_size_cm), _MIN_TRAY_SIZE_CM) / 100.0
    radius_m = tray_size_m / 2.0
    linear_speed_m_s = tray_size_m / safe_sec_per_tray
    return linear_speed_m_s / radius_m


def velocity_rad_s_to_sec_per_tray(
    velocity_rad_s: float,
    *,
    tray_size_cm: float,
) -> float | None:
    tray_size_m = max(float(tray_size_cm), _MIN_TRAY_SIZE_CM) / 100.0
    radius_m = tray_size_m / 2.0
    tangential_speed_m_s = abs(float(velocity_rad_s)) * radius_m
    if tangential_speed_m_s <= _EPSILON:
        return None
    return tray_size_m / tangential_speed_m_s


def velocity_rad_s_to_trays_per_second(
    velocity_rad_s: float,
    *,
    tray_size_cm: float,
) -> float | None:
    sec_per_tray = velocity_rad_s_to_sec_per_tray(
        velocity_rad_s,
        tray_size_cm=tray_size_cm,
    )
    if sec_per_tray is None:
        return None
    return sec_per_tray_to_trays_per_second(sec_per_tray)
