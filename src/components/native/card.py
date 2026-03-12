import flet as ft

from theme import colors, radius, shadows, spacing


def TangoCard(
    *,
    content: ft.Control,
    padding: ft.Padding | int | None = None,
    expand: bool = False,
    width: int | None = None,
    height: int | None = None,
    border_radius: int | None = None,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding or spacing.SM,
        expand=expand,
        width=width,
        height=height,
        bgcolor=colors.SURFACE,
        border_radius=border_radius or radius.PANEL,
        border=ft.Border.all(1, colors.OUTLINE_STRONG),
        shadow=shadows.card_shadow(),
    )
