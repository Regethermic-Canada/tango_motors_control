from dataclasses import dataclass
import flet as ft
from utils.config import config


@dataclass(frozen=True)
class ViewportMetrics:
    width: float
    height: float
    scale: float
    is_compact: bool


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def get_viewport_metrics(
    page: ft.Page,
    *,
    base_width: float | None = None,
    base_height: float | None = None,
    min_scale: float = 0.7,
    max_scale: float = 1.0,
    fallback_width: float | None = None,
    fallback_height: float | None = None,
) -> ViewportMetrics:
    resolved_base_width = float(base_width or config.app_screen_width)
    resolved_base_height = float(base_height or config.app_screen_height)
    resolved_fallback_width = float(fallback_width or config.app_screen_width)
    resolved_fallback_height = float(fallback_height or config.app_screen_height)
    compact_max_width = float(
        max(config.app_screen_width + 100, config.app_screen_width * 1.125)
    )
    compact_max_height = float(
        max(config.app_screen_height + 40, config.app_screen_height * 1.08)
    )

    width = float(
        getattr(page, "width", resolved_fallback_width) or resolved_fallback_width
    )
    height = float(
        getattr(page, "height", resolved_fallback_height) or resolved_fallback_height
    )
    scale = clamp(
        min(width / resolved_base_width, height / resolved_base_height),
        min_scale,
        max_scale,
    )
    is_compact = height <= compact_max_height or width <= compact_max_width
    return ViewportMetrics(
        width=width,
        height=height,
        scale=scale,
        is_compact=is_compact,
    )
