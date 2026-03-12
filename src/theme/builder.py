from pathlib import Path

import flet as ft

from . import colors, radius, typography


def build_theme() -> ft.Theme:
    return ft.Theme(
        font_family=typography.FONT_FAMILY,
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=colors.PRIMARY,
            on_primary=colors.TEXT_INVERSE,
            primary_container=colors.PRIMARY_SOFT,
            on_primary_container=colors.PRIMARY,
            secondary=colors.PRIMARY_DARK,
            on_secondary=colors.TEXT_INVERSE,
            secondary_container=colors.PRIMARY_SOFT,
            on_secondary_container=colors.PRIMARY,
            error=colors.ERROR,
            on_error=colors.TEXT_INVERSE,
            error_container=colors.ERROR_SOFT,
            on_error_container=colors.ERROR,
            surface=colors.SURFACE,
            on_surface=colors.TEXT,
            on_surface_variant=colors.TEXT_MUTED,
            outline=colors.OUTLINE,
            outline_variant=colors.OUTLINE_STRONG,
            shadow="#140B264F",
            surface_tint=colors.PRIMARY,
        ),
        scaffold_bgcolor=colors.APP_BACKGROUND,
        card_bgcolor=colors.SURFACE,
        divider_color=colors.OUTLINE,
        splash_color="#142069D8",
        hover_color="#0F2069D8",
        highlight_color="#142069D8",
        focus_color="#142069D8",
        text_theme=ft.TextTheme(
            display_large=typography.text_style("display"),
            display_medium=typography.text_style("headline"),
            headline_medium=typography.text_style("title"),
            title_large=typography.text_style("subtitle"),
            body_large=typography.text_style("body"),
            body_medium=typography.text_style("body"),
            label_large=typography.text_style("label"),
            label_medium=typography.text_style("caption"),
        ),
        card_theme=ft.CardTheme(
            color=colors.SURFACE,
            shadow_color="#140B264F",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=radius.PANEL),
        ),
        progress_indicator_theme=ft.ProgressIndicatorTheme(
            color=colors.PRIMARY,
            circular_track_color=colors.PRIMARY_BORDER,
            linear_track_color=colors.PRIMARY_BORDER,
            stroke_width=6,
        ),
        slider_theme=ft.SliderTheme(
            active_track_color=colors.PRIMARY,
            inactive_track_color=colors.PRIMARY_BORDER,
            active_tick_mark_color=colors.PRIMARY_BORDER,
            inactive_tick_mark_color=colors.PRIMARY_BORDER,
            thumb_color=colors.PRIMARY_DARK,
            overlay_color="#142069D8",
            value_indicator_color=colors.PRIMARY_DARK,
            value_indicator_text_style=typography.text_style(
                "caption", color=colors.TEXT_INVERSE
            ),
            track_height=4,
        ),
        filled_button_theme=ft.FilledButtonTheme(
            style=ft.ButtonStyle(
                bgcolor=colors.PRIMARY,
                color=colors.TEXT_INVERSE,
                side=ft.BorderSide(1, colors.PRIMARY),
                padding=ft.Padding(16, 10, 16, 10),
                shape=ft.RoundedRectangleBorder(radius=radius.BUTTON),
            )
        ),
        icon_button_theme=ft.IconButtonTheme(
            style=ft.ButtonStyle(
                bgcolor=colors.SURFACE,
                icon_color=colors.TEXT,
                side=ft.BorderSide(1, colors.OUTLINE),
                shape=ft.RoundedRectangleBorder(radius=radius.BUTTON),
            )
        ),
        tooltip_theme=ft.TooltipTheme(
            wait_duration=250,
            show_duration=4000,
            prefer_below=False,
            vertical_offset=20,
            padding=ft.Padding(10, 6, 10, 6),
            text_style=typography.text_style("caption", color=colors.TEXT_INVERSE),
            decoration=ft.BoxDecoration(
                bgcolor=colors.PRIMARY_DARK,
                border_radius=radius.SM,
            ),
        ),
    )


def configure_page(page: ft.Page) -> None:
    assets_root = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    regular_font = assets_root / "Manrope-Regular.ttf"
    medium_font = assets_root / "Manrope-Medium.ttf"

    if regular_font.exists() and medium_font.exists():
        page.fonts = {
            typography.FONT_FAMILY: "fonts/Manrope-Regular.ttf",
            typography.FONT_FAMILY_MEDIUM: "fonts/Manrope-Medium.ttf",
        }

    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = build_theme()
