import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any
import flet as ft


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
    if existing and existing.container in page.overlay:
        page.overlay.remove(existing.container)

    close_token = int(time.monotonic_ns())

    def close_toast(_: Any = None) -> None:
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

    toast_container = ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, color="white", size=28),
                ft.VerticalDivider(width=1, color="white24"),
                ft.Text(
                    message,
                    color="white",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color="white",
                    icon_size=24,
                    tooltip=close_tooltip,
                    on_click=close_toast,
                ),
            ],
            tight=True,
            spacing=15,
        ),
        bgcolor=bg_color,
        padding=ft.Padding(25, 15, 20, 15),
        border_radius=12,
        width=400,
        shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color="black26"),
        animate_opacity=300,
        animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        opacity=0,
        offset=ft.Offset(0, -1),
        top=position_top,
        right=position_right,
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
