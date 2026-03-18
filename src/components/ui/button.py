import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.button import Button
from typing import Literal

from .text import TangoText
from theme import colors, radius

ControlHandler = ControlEventHandler[Button] | None
ButtonVariant = Literal["primary", "secondary", "surface"]
ButtonSize = Literal["sm", "md", "lg"]

_HEIGHTS = {
    "sm": 36,
    "md": 46,
    "lg": 52,
}


_PADDING = {
    "sm": (12, 8),
    "md": (16, 10),
    "lg": (20, 12),
}

_VARIANT_STYLES: dict[ButtonVariant, tuple[str, str, str]] = {
    "primary": (colors.PRIMARY, colors.TEXT_INVERSE, colors.PRIMARY),
    "secondary": (colors.PRIMARY_SOFT, colors.PRIMARY, colors.PRIMARY_SOFT),
    "surface": (colors.SURFACE, colors.TEXT, colors.OUTLINE),
}


def TangoButton(
    text: str,
    *,
    on_click: ControlHandler = None,
    variant: ButtonVariant = "primary",
    size: ButtonSize = "md",
    expand: bool = False,
    icon: ft.IconData | None = None,
    tooltip: str | None = None,
    disabled: bool = False,
    width: int | None = None,
    text_size: int | None = None,
) -> ft.FilledButton:
    background, foreground, border_color = _VARIANT_STYLES[variant]
    pad_x, pad_y = _PADDING[size]
    resolved_height = _HEIGHTS[size]
    return ft.FilledButton(
        expand=expand,
        width=width,
        icon=icon,
        tooltip=tooltip,
        disabled=disabled,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor=background,
            color=foreground,
            side=ft.BorderSide(1, border_color),
            padding=ft.Padding(pad_x, pad_y, pad_x, pad_y),
            shape=ft.RoundedRectangleBorder(radius=radius.BUTTON),
        ),
        content=TangoText(
            text,
            variant="label",
            color=foreground,
            size=text_size or (17 if size == "lg" else 16),
            text_align=ft.TextAlign.CENTER,
        ),
        height=resolved_height,
    )
