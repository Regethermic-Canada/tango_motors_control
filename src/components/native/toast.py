import asyncio
import time
from dataclasses import dataclass
from enum import Enum
import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton

from .icon_button import TangoIconButton
from .text import TangoText
from theme import colors, radius, shadows
from theme.scale import get_viewport_metrics


class ToastType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class _ToastRuntime:
    container: ft.Container
    close_token: int


_active_toasts: dict[int, _ToastRuntime] = {}
_last_toast_at: dict[tuple[int, str], float] = {}
ControlHandler = ControlEventHandler[IconButton] | None


def TangoToast(
    *,
    message: str,
    type: ToastType,
    close_tooltip: str,
    compact: bool,
    metrics_scale: float,
    width: int,
    top: int,
    right: int,
    on_close: ControlHandler = None,
) -> ft.Container:
    toast_icon_size = int(round((22 if compact else 28) * metrics_scale))
    toast_text_size = int(round((14 if compact else 16) * metrics_scale))
    row_spacing = int(round((8 if compact else 12) * metrics_scale))
    pad_h_left = int(round((12 if compact else 16) * metrics_scale))
    pad_v = int(round((8 if compact else 10) * metrics_scale))
    pad_h_right = int(round((8 if compact else 12) * metrics_scale))

    palette = {
        ToastType.SUCCESS: (colors.SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE),
        ToastType.ERROR: (colors.ERROR, ft.Icons.ERROR_OUTLINE),
        ToastType.WARNING: (colors.WARNING_DARK, ft.Icons.WARNING_AMBER_OUTLINED),
        ToastType.INFO: (colors.PRIMARY, ft.Icons.INFO_OUTLINE),
    }
    bg_color, icon = palette.get(type, palette[ToastType.INFO])

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, color=colors.TEXT_INVERSE, size=toast_icon_size),
                ft.VerticalDivider(width=1, color="#33FFFFFF"),
                TangoText(
                    message,
                    variant="body_strong",
                    color=colors.TEXT_INVERSE,
                    size=toast_text_size,
                    expand=True,
                ),
                TangoIconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip=close_tooltip,
                    on_click=on_close,
                    icon_size=int(round((14 if compact else 16) * metrics_scale)),
                    variant="inverse",
                    size="sm",
                ),
            ],
            tight=True,
            spacing=row_spacing,
        ),
        bgcolor=bg_color,
        padding=ft.Padding(pad_h_left, pad_v, pad_h_right, pad_v),
        border_radius=radius.TOAST,
        width=width,
        shadow=shadows.card_shadow(metrics_scale),
        animate_opacity=300,
        animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        opacity=0,
        offset=ft.Offset(0, -1),
        top=top,
        right=right,
    )


def show_toast(
    page: ft.Page,
    message: str,
    type: ToastType = ToastType.ERROR,
    duration: float = 3.0,
    position_top: int = 80,
    position_right: int = 20,
    close_tooltip: str = "Close",
    dedupe_window_s: float = 1.5,
) -> None:
    metrics = get_viewport_metrics(page, min_scale=0.66)
    compact = metrics.compact
    resolved_top = getattr(page, "_tango_toast_top_offset", None)
    resolved_right = getattr(page, "_tango_toast_right_offset", None)
    toast_width = min(
        280 if compact else 400,
        max(220, int(metrics.width - (position_right * 2) - 8)),
    )
    top_offset = (
        int(resolved_top)
        if isinstance(resolved_top, int | float)
        else int(round(position_top * metrics.scale))
    )
    right_offset = (
        int(resolved_right)
        if isinstance(resolved_right, int | float)
        else int(round(position_right * metrics.scale))
    )

    page_key = id(page)
    toast_key = f"{type.value}:{message}"
    now = time.monotonic()
    last_shown = _last_toast_at.get((page_key, toast_key))
    if last_shown is not None and (now - last_shown) < dedupe_window_s:
        return
    _last_toast_at[(page_key, toast_key)] = now

    existing = _active_toasts.get(page_key)
    if existing and existing.container in page.overlay:
        page.overlay.remove(existing.container)

    close_token = int(time.monotonic_ns())

    def close_toast() -> None:
        current = _active_toasts.get(page_key)
        if current is None or current.close_token != close_token:
            return
        toast_container = current.container
        if toast_container not in page.overlay:
            return

        toast_container.opacity = 0
        toast_container.offset = ft.Offset(0, -1)
        page.update()

        async def remove() -> None:
            await asyncio.sleep(0.3)
            still_current = _active_toasts.get(page_key)
            if still_current is None or still_current.close_token != close_token:
                return
            if toast_container in page.overlay:
                page.overlay.remove(toast_container)
                page.update()
            _active_toasts.pop(page_key, None)

        asyncio.create_task(remove())

    toast_container = TangoToast(
        message=message,
        type=type,
        close_tooltip=close_tooltip,
        compact=compact,
        metrics_scale=metrics.scale,
        width=toast_width,
        top=top_offset,
        right=right_offset,
        on_close=lambda _: close_toast(),
    )

    _active_toasts[page_key] = _ToastRuntime(
        container=toast_container,
        close_token=close_token,
    )
    page.overlay.append(toast_container)
    page.update()
    toast_container.opacity = 1
    toast_container.offset = ft.Offset(0, 0)
    page.update()

    async def auto_hide() -> None:
        await asyncio.sleep(duration)
        close_toast()

    asyncio.create_task(auto_hide())
