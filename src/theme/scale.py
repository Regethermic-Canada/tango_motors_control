from dataclasses import dataclass
from enum import StrEnum

import flet as ft

from utils.config import config


class ViewportArea(StrEnum):
    PAGE = "page"
    CONTENT = "content"


@dataclass(frozen=True)
class ViewportMetrics:
    width: float
    height: float
    scale: float
    is_compact: bool


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def resolve_panel_width(
    metrics: ViewportMetrics,
    *,
    compact_fraction: float,
    regular_fraction: float,
    compact_min: int,
    regular_min: int,
    max_width: int,
    edge_padding: int = 0,
) -> int:
    min_width = compact_min if metrics.is_compact else regular_min
    width_fraction = compact_fraction if metrics.is_compact else regular_fraction
    available_width = max(0, int(metrics.width) - (edge_padding * 2))
    target_width = max(min_width, int(metrics.width * width_fraction))
    return min(max_width, available_width or max_width, target_width)


def _resolve_page_dimension(
    page: ft.Page,
    attr_name: str,
    fallback: float,
) -> float:
    return float(getattr(page, attr_name, fallback) or fallback)


def _resolve_viewport_height(
    page: ft.Page,
    *,
    area: ViewportArea,
    fallback_height: float,
) -> float:
    total_height = _resolve_page_dimension(page, "height", fallback_height)
    if area is ViewportArea.PAGE:
        return total_height

    top_inset = float(getattr(page, "_tango_content_top_inset", 0) or 0)
    bottom_inset = float(getattr(page, "_tango_content_bottom_inset", 0) or 0)
    return max(1.0, total_height - top_inset - bottom_inset)


def _build_viewport_metrics(
    *,
    width: float,
    height: float,
    base_width: float,
    base_height: float,
    min_scale: float,
    max_scale: float,
) -> ViewportMetrics:
    compact_max_width = float(
        max(config.app_screen_width + 100, config.app_screen_width * 1.125)
    )
    compact_max_height = float(
        max(config.app_screen_height + 40, config.app_screen_height * 1.08)
    )
    scale = clamp(
        min(width / base_width, height / base_height),
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


def get_viewport_metrics(
    page: ft.Page,
    *,
    area: ViewportArea = ViewportArea.PAGE,
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
    width = _resolve_page_dimension(page, "width", resolved_fallback_width)
    height = _resolve_viewport_height(
        page,
        area=area,
        fallback_height=resolved_fallback_height,
    )
    return _build_viewport_metrics(
        width=width,
        height=height,
        base_width=resolved_base_width,
        base_height=resolved_base_height,
        min_scale=min_scale,
        max_scale=max_scale,
    )
