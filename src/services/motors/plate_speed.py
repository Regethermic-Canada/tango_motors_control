from __future__ import annotations

_MIN_PLATE_SIZE_CM = 0.1
_EPSILON = 1e-9


def clamp_sec_per_plate(
    sec_per_plate: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    low = min(minimum, maximum)
    high = max(minimum, maximum)
    return max(low, min(float(sec_per_plate), high))


def sec_per_plate_to_plates_per_second(sec_per_plate: float) -> float:
    safe_sec_per_plate = max(float(sec_per_plate), _EPSILON)
    return 1.0 / safe_sec_per_plate


def sec_per_plate_to_velocity_rad_s(
    sec_per_plate: float,
    *,
    plate_size_cm: float,
) -> float:
    # The plate-time target is treated as tangential travel of one plate length
    # across a plate with the configured diameter.
    safe_sec_per_plate = max(float(sec_per_plate), _EPSILON)
    plate_size_m = max(float(plate_size_cm), _MIN_PLATE_SIZE_CM) / 100.0
    radius_m = plate_size_m / 2.0
    linear_speed_m_s = plate_size_m / safe_sec_per_plate
    return linear_speed_m_s / radius_m


def velocity_rad_s_to_sec_per_plate(
    velocity_rad_s: float,
    *,
    plate_size_cm: float,
) -> float | None:
    plate_size_m = max(float(plate_size_cm), _MIN_PLATE_SIZE_CM) / 100.0
    radius_m = plate_size_m / 2.0
    tangential_speed_m_s = abs(float(velocity_rad_s)) * radius_m
    if tangential_speed_m_s <= _EPSILON:
        return None
    return plate_size_m / tangential_speed_m_s


def velocity_rad_s_to_plates_per_second(
    velocity_rad_s: float,
    *,
    plate_size_cm: float,
) -> float | None:
    sec_per_plate = velocity_rad_s_to_sec_per_plate(
        velocity_rad_s,
        plate_size_cm=plate_size_cm,
    )
    if sec_per_plate is None:
        return None
    return sec_per_plate_to_plates_per_second(sec_per_plate)
