import flet as ft

from .text import TangoText
from theme import colors, spacing


def TangoSectionHeader(
    *,
    title: str,
    subtitle: str | None = None,
    actions: list[ft.Control] | None = None,
    title_size: int | None = None,
) -> ft.Control:
    text_controls: list[ft.Control] = [
        TangoText(title, variant="title", size=title_size),
    ]
    if subtitle:
        text_controls.append(
            TangoText(subtitle, variant="body", size=14, color=colors.TEXT_MUTED)
        )

    content = ft.Column(
        spacing=spacing.XXS,
        controls=text_controls,
    )

    if not actions:
        return content

    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[content, ft.Row(tight=True, spacing=spacing.XS, controls=actions)],
    )
