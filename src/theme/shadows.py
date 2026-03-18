import flet as ft

from . import colors


def card_shadow(scale: float = 1.0) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=18 * scale,
        spread_radius=0,
        offset=ft.Offset(0, 6 * scale),
        color=colors.SHADOW_STRONG,
    )


def soft_shadow(scale: float = 1.0) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=10 * scale,
        spread_radius=0,
        offset=ft.Offset(0, 3 * scale),
        color=colors.SHADOW_SOFT,
    )
