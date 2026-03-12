import flet as ft

from theme import typography


def TangoText(
    value: str,
    *,
    variant: typography.TextVariant = "body",
    color: str | None = None,
    size: int | None = None,
    weight: ft.FontWeight | None = None,
    text_align: ft.TextAlign | None = None,
    expand: bool | None = None,
    letter_spacing: float | None = None,
) -> ft.Text:
    style = typography.text_style(
        variant,
        color=color,
        size=size,
        weight=weight,
        letter_spacing=letter_spacing,
    )
    return ft.Text(
        value=value,
        style=style,
        text_align=text_align or ft.TextAlign.START,
        expand=expand,
    )
