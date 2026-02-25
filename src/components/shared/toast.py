import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any
import flet as ft
from utils.ui_scale import get_viewport_metrics


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
_toast_hosts: dict[int, ft.Stack] = {}


def ensure_toast_overlay_host(page: ft.Page) -> ft.Stack:
    page_key = id(page)
    host = _toast_hosts.get(page_key)
    if host is not None and host in page.overlay:
        return host

    host = ft.Stack(expand=True, controls=[])
    _toast_hosts[page_key] = host
    page.overlay.append(host)
    return host


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
    host = ensure_toast_overlay_host(page)

    toast_width = min(
        280 if compact else 400,
        max(220, int(metrics.width - (position_right * 2) - 8)),
    )
    toast_icon_size = int(round((22 if compact else 28) * metrics.scale))
    toast_text_size = int(round((15 if compact else 18) * metrics.scale))
    close_icon_size = int(round((18 if compact else 24) * metrics.scale))
    row_spacing = int(round((8 if compact else 15) * metrics.scale))
    pad_h_left = int(round((12 if compact else 25) * metrics.scale))
    pad_v = int(round((8 if compact else 15) * metrics.scale))
    pad_h_right = int(round((8 if compact else 20) * metrics.scale))
    border_radius = int(round((10 if compact else 12) * metrics.scale))
    shadow_blur = int(round(15 * metrics.scale))
    top_offset = int(round(position_top * metrics.scale))
    right_offset = int(round(position_right * metrics.scale))
    close_button_padding = int(round((2 if compact else 8) * metrics.scale))

    page_key = id(page)
    toast_key = f"{type.value}:{message}"
    now = time.monotonic()
    last_shown = _last_toast_at.get((page_key, toast_key))
    if last_shown is not None and (now - last_shown) < dedupe_window_s:
        return
    _last_toast_at[(page_key, toast_key)] = now

    colors = {
        ToastType.SUCCESS: ("green600", ft.Icons.CHECK_CIRCLE_OUTLINE),
        ToastType.ERROR: ("red600", ft.Icons.ERROR_OUTLINE),
        ToastType.WARNING: ("amber600", ft.Icons.WARNING_AMBER_OUTLINED),
        ToastType.INFO: ("blue600", ft.Icons.INFO_OUTLINE),
    }

    bg_color, icon = colors.get(type, colors[ToastType.INFO])

    existing = _active_toasts.get(page_key)
    if existing and existing.container in host.controls:
        host.controls.remove(existing.container)

    close_token = int(time.monotonic_ns())

    def close_toast(_: Any = None) -> None:
        current = _active_toasts.get(page_key)
        if current is None or current.close_token != close_token:
            return
        toast_container = current.container
        if toast_container not in host.controls:
            return

        toast_container.opacity = 0
        toast_container.offset = ft.Offset(0, -1)
        page.update()

        async def remove() -> None:
            await asyncio.sleep(0.3)
            still_current = _active_toasts.get(page_key)
            if still_current is None or still_current.close_token != close_token:
                return
            if toast_container in host.controls:
                host.controls.remove(toast_container)
                page.update()
            _active_toasts.pop(page_key, None)

        asyncio.create_task(remove())

    toast_container = ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, color="white", size=toast_icon_size),
                ft.VerticalDivider(width=1, color="white24"),
                ft.Text(
                    message,
                    color="white",
                    size=toast_text_size,
                    weight=ft.FontWeight.W_600,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color="white",
                    icon_size=close_icon_size,
                    tooltip=close_tooltip,
                    on_click=close_toast,
                    style=ft.ButtonStyle(
                        padding=ft.Padding(
                            close_button_padding,
                            close_button_padding,
                            close_button_padding,
                            close_button_padding,
                        )
                    ),
                ),
            ],
            tight=True,
            spacing=row_spacing,
        ),
        bgcolor=bg_color,
        padding=ft.Padding(pad_h_left, pad_v, pad_h_right, pad_v),
        border_radius=border_radius,
        width=toast_width,
        shadow=ft.BoxShadow(blur_radius=shadow_blur, spread_radius=1, color="black26"),
        animate_opacity=300,
        animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        opacity=0,
        offset=ft.Offset(0, -1),
        top=top_offset,
        right=right_offset,
    )

    _active_toasts[page_key] = _ToastRuntime(
        container=toast_container,
        close_token=close_token,
    )
    host.controls.append(toast_container)
    page.update()
    toast_container.opacity = 1
    toast_container.offset = ft.Offset(0, 0)
    page.update()

    async def auto_hide() -> None:
        await asyncio.sleep(duration)
        close_toast()

    asyncio.create_task(auto_hide())
