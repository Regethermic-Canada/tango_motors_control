import flet as ft

from theme import colors, radius, shadows, spacing


def _resolve_padding(padding: ft.Padding | int | None) -> ft.Padding:
    if isinstance(padding, int):
        return ft.Padding(padding, padding, padding, padding)
    if padding is None:
        default_padding = spacing.SM
        return ft.Padding(
            default_padding,
            default_padding,
            default_padding,
            default_padding,
        )
    return padding


def TangoCard(
    *,
    content: ft.Control,
    padding: ft.Padding | int | None = None,
    expand: bool = False,
    scrollable: bool = False,
    width: int | None = None,
    height: int | None = None,
    border_radius: int | None = None,
) -> ft.Container:
    body_padding = _resolve_padding(padding)
    body_content: ft.Control
    if scrollable:
        body_content = ft.Container(
            expand=True,
            content=ft.ListView(
                expand=True,
                auto_scroll=False,
                scroll=ft.ScrollMode.ALWAYS,
                spacing=0,
                controls=[
                    ft.Container(
                        content=content,
                        padding=ft.Padding(
                            body_padding.left,
                            body_padding.top,
                            body_padding.right + spacing.LG,
                            body_padding.bottom,
                        ),
                    )
                ],
            ),
        )
    else:
        body_content = ft.Container(
            content=content,
            padding=body_padding,
        )

    return ft.Container(
        content=body_content,
        expand=expand,
        width=width,
        height=height,
        bgcolor=colors.SURFACE,
        border_radius=border_radius or radius.PANEL,
        border=ft.Border.all(1, colors.OUTLINE_STRONG),
        shadow=shadows.card_shadow(1.3),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
