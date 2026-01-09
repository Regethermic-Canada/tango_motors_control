import asyncio
from enum import Enum
from typing import Any, Optional
import flet as ft


class ToastType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def show_toast(
    page: ft.Page,
    message: str,
    type: ToastType = ToastType.ERROR,
    duration: int = 3,
    position_top: int = 80,
    position_right: int = 20,
    close_tooltip: str = "Close",
) -> None:

    # Define styles based on type
    colors = {
        ToastType.SUCCESS: ("green600", ft.Icons.CHECK_CIRCLE_OUTLINE),
        ToastType.ERROR: ("red600", ft.Icons.ERROR_OUTLINE),
        ToastType.WARNING: ("amber600", ft.Icons.WARNING_AMBER_OUTLINED),
        ToastType.INFO: ("blue600", ft.Icons.INFO_OUTLINE),
    }

    bg_color, icon = colors.get(type, colors[ToastType.INFO])

    toast_container: Optional[ft.Container] = None

    def close_toast(e: Any = None) -> None:
        nonlocal toast_container
        if toast_container and toast_container in page.overlay:
            toast_container.opacity = 0
            toast_container.offset = ft.Offset(0, -1)
            page.update()

            # Wait for animation before removing
            async def remove() -> None:
                await asyncio.sleep(0.3)
                if toast_container in page.overlay:
                    page.overlay.remove(toast_container)
                    page.update()

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

    page.overlay.append(toast_container)
    page.update()

    # Animate In
    toast_container.opacity = 1
    toast_container.offset = ft.Offset(0, 0)
    page.update()

    async def auto_hide() -> None:
        await asyncio.sleep(duration)
        close_toast()

    asyncio.create_task(auto_hide())
