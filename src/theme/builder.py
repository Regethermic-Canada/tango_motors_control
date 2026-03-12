from pathlib import Path

import flet as ft

from . import typography


def configure_page(page: ft.Page) -> None:
    assets_root = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    regular_font = assets_root / "Manrope-Regular.ttf"
    medium_font = assets_root / "Manrope-Medium.ttf"

    if regular_font.exists() and medium_font.exists():
        page.fonts = {
            typography.FONT_FAMILY: "fonts/Manrope-Regular.ttf",
            f"{typography.FONT_FAMILY} Medium": "fonts/Manrope-Medium.ttf",
        }

    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family=typography.FONT_FAMILY)
