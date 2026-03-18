import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton
from typing import Literal

from theme import colors, radius

ControlHandler = ControlEventHandler[IconButton] | None
IconButtonVariant = Literal["primary", "secondary", "surface", "inverse"]
IconButtonSize = Literal["sm", "md", "lg"]

_SIZE_MAP = {
    "sm": (32, 14),
    "md": (40, 18),
    "lg": (48, 22),
}

_VARIANT_STYLES: dict[IconButtonVariant, tuple[str, str, str]] = {
    "primary": (colors.PRIMARY, colors.PRIMARY, colors.TEXT_INVERSE),
    "surface": (colors.SURFACE, colors.OUTLINE, colors.TEXT),
    "secondary": (colors.PRIMARY_SOFT, colors.PRIMARY_SOFT, colors.PRIMARY),
    "inverse": ("#1FFFFFFF", "#33FFFFFF", colors.TEXT_INVERSE),
}


def TangoIconButton(
    *,
    icon: ft.IconData,
    on_click: ControlHandler = None,
    tooltip: str | None = None,
    icon_size: int | None = None,
    variant: IconButtonVariant = "surface",
    size: IconButtonSize = "md",
    disabled: bool = False,
) -> ft.IconButton:
    diameter, default_icon_size = _SIZE_MAP[size]
    resolved_icon_size = icon_size or default_icon_size
    bgcolor, border_color, icon_color = _VARIANT_STYLES[variant]

    return ft.IconButton(
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        disabled=disabled,
        icon_size=resolved_icon_size,
        icon_color=icon_color,
        width=diameter,
        height=diameter,
        disabled_color=colors.TEXT_SOFT,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: bgcolor,
                ft.ControlState.DISABLED: colors.SURFACE_SUBTLE,
            },
            icon_color={
                ft.ControlState.DEFAULT: icon_color,
                ft.ControlState.DISABLED: colors.TEXT_SOFT,
            },
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, border_color),
                ft.ControlState.DISABLED: ft.BorderSide(1, colors.OUTLINE),
            },
            shape=ft.RoundedRectangleBorder(radius=radius.BUTTON),
            animation_duration=180,
        ),
    )
