from dataclasses import dataclass
import flet as ft


@dataclass(frozen=True)
class ViewportMetrics:
    width: float
    height: float
    scale: float
    compact: bool


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def get_viewport_metrics(
    page: ft.Page,
    *,
    base_width: float = 1280,
    base_height: float = 720,
    min_scale: float = 0.7,
    max_scale: float = 1.0,
    compact_max_width: float = 900,
    compact_max_height: float = 520,
    fallback_width: float = 800,
    fallback_height: float = 480,
) -> ViewportMetrics:
    width = float(getattr(page, "width", fallback_width) or fallback_width)
    height = float(getattr(page, "height", fallback_height) or fallback_height)
    scale = clamp(min(width / base_width, height / base_height), min_scale, max_scale)
    compact = height <= compact_max_height or width <= compact_max_width
    return ViewportMetrics(width=width, height=height, scale=scale, compact=compact)
