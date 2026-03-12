import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.container import Container

from theme import colors, radius, shadows

ControlHandler = ControlEventHandler[Container] | None


def TangoNavItem(
    *,
    icon: ft.IconData,
    selected_icon: ft.IconData | None = None,
    selected: bool = False,
    tooltip: str | None = None,
    icon_size: int = 22,
    size: int = 56,
    on_click: ControlHandler = None,
) -> ft.Container:
    active_icon = selected_icon if selected and selected_icon else icon
    return ft.Container(
        ink=True,
        width=size,
        height=size,
        alignment=ft.Alignment.CENTER,
        border_radius=radius.BUTTON,
        tooltip=tooltip,
        bgcolor=colors.PRIMARY if selected else colors.SURFACE,
        border=ft.border.all(1, colors.PRIMARY if selected else colors.OUTLINE),
        shadow=shadows.soft_shadow(),
        content=ft.Row(
            [
                ft.Icon(
                    active_icon,
                    size=icon_size,
                    color=colors.TEXT_INVERSE if selected else colors.TEXT,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=on_click,
    )
