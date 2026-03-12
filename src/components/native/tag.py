import flet as ft
from typing import Literal

from .text import TangoText
from theme import colors, radius

TagVariant = Literal["primary", "secondary", "success", "warning", "error", "neutral"]

_TAG_VARIANTS = {
    "primary": (colors.PRIMARY, colors.TEXT_INVERSE, colors.PRIMARY),
    "secondary": (colors.PRIMARY_SOFT, colors.PRIMARY, colors.PRIMARY_SOFT),
    "success": (colors.SUCCESS, colors.TEXT_INVERSE, colors.SUCCESS),
    "warning": (colors.WARNING, colors.WARNING_DARK, colors.WARNING),
    "error": (colors.ERROR, colors.TEXT_INVERSE, colors.ERROR),
    "neutral": (colors.SURFACE_SUBTLE, colors.TEXT_MUTED, colors.OUTLINE),
}


def TangoTag(
    label: str,
    *,
    variant: TagVariant = "secondary",
    min_width: int = 40,
) -> ft.Container:
    bgcolor, text_color, border_color = _TAG_VARIANTS[variant]
    return ft.Container(
        bgcolor=bgcolor,
        border_radius=radius.TAG,
        border=ft.border.all(1, border_color),
        padding=ft.Padding(8, 6, 8, 6),
        height=40,
        alignment=ft.Alignment.CENTER,
        width=max(min_width, 40) if len(label) <= 2 else None,
        content=TangoText(
            label,
            variant="label",
            color=text_color,
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
    )
