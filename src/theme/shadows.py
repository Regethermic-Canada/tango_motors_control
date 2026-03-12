import flet as ft


def card_shadow(scale: float = 1.0) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=18 * scale,
        spread_radius=0,
        offset=ft.Offset(0, 6 * scale),
        color="#140B264F",
    )


def soft_shadow(scale: float = 1.0) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=10 * scale,
        spread_radius=0,
        offset=ft.Offset(0, 3 * scale),
        color="#100B264F",
    )
