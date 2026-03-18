import flet as ft

from theme import spacing


def TangoPage(
    *,
    content: ft.Control,
    padding: ft.Padding | int | None = None,
    expand: bool = True,
    alignment: ft.Alignment | None = None,
    width: int | None = None,
) -> ft.Container:
    return ft.Container(
        expand=expand,
        width=width,
        alignment=alignment,
        padding=padding or spacing.MD,
        content=content,
    )
