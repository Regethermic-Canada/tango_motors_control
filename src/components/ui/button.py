import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.button import Button
from typing import Literal

from .text import TangoText
from theme import colors, radius

ControlHandler = ControlEventHandler[Button] | None
ButtonVariant = Literal["primary", "secondary", "surface"]
ButtonSize = Literal["sm", "md", "lg", "xl"]

_HEIGHTS = {
    "sm": 36,
    "md": 46,
    "lg": 52,
    "xl": 72,
}


_PADDING = {
    "sm": (12, 8),
    "md": (16, 10),
    "lg": (20, 12),
    "xl": (28, 16),
}

_VARIANT_STYLES: dict[ButtonVariant, tuple[str, str, str]] = {
    "primary": (colors.PRIMARY, colors.TEXT_INVERSE, colors.PRIMARY),
    "secondary": (colors.PRIMARY_SOFT, colors.PRIMARY, colors.PRIMARY_SOFT),
    "surface": (colors.SURFACE, colors.TEXT, colors.OUTLINE),
}


def TangoButton(
    text: str | None = None,
    *,
    on_click: ControlHandler = None,
    variant: ButtonVariant = "primary",
    size: ButtonSize = "md",
    expand: bool = False,
    icon: ft.IconData | None = None,
    icon_only: bool = False,
    icon_size: int | None = None,
    tooltip: str | None = None,
    disabled: bool = False,
    width: int | None = None,
    text_size: int | None = None,
) -> ft.FilledButton:
    background, foreground, border_color = _VARIANT_STYLES[variant]
    pad_x, pad_y = _PADDING[size]
    resolved_height = _HEIGHTS[size]
    resolved_icon_size = icon_size or (
        32 if size == "xl" else 22 if size == "lg" else 20
    )
    content: ft.Control
    button_icon: ft.IconData | None = None
    resolved_text_size = text_size or (
        22 if size == "xl" else 17 if size == "lg" else 16
    )
    if icon_only and icon is not None:
        content = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                icon,
                color=foreground,
                size=resolved_icon_size,
            ),
        )
    elif icon is not None:
        icon_left_padding = 8 if size == "sm" else 10 if size == "md" else 12
        content = ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=TangoText(
                        text or "",
                        variant="label",
                        color=foreground,
                        size=resolved_text_size,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                ft.Container(
                    left=icon_left_padding,
                    top=0,
                    bottom=0,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Icon(
                        icon,
                        color=foreground,
                        size=resolved_icon_size,
                    ),
                ),
            ],
        )
    else:
        content = TangoText(
            text or "",
            variant="label",
            color=foreground,
            size=resolved_text_size,
            text_align=ft.TextAlign.CENTER,
        )

    return ft.FilledButton(
        expand=expand,
        width=width,
        icon=button_icon,
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
        content=content,
        height=resolved_height,
    )
