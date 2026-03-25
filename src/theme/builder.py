from pathlib import Path

import flet as ft

from . import animation, colors, radius, typography


def _button_shape(corner_radius: int) -> ft.RoundedRectangleBorder:
    return ft.RoundedRectangleBorder(radius=corner_radius)


def _color_scheme() -> ft.ColorScheme:
    return ft.ColorScheme(
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
        shadow=colors.SHADOW_STRONG,
        surface_tint=colors.PRIMARY,
    )


def _text_theme() -> ft.TextTheme:
    return ft.TextTheme(
        display_large=typography.text_style("display"),
        display_medium=typography.text_style("headline"),
        headline_medium=typography.text_style("title"),
        title_large=typography.text_style("subtitle"),
        body_large=typography.text_style("body"),
        body_medium=typography.text_style("body"),
        label_large=typography.text_style("label"),
        label_medium=typography.text_style("caption"),
    )


def _filled_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=colors.PRIMARY,
        color=colors.TEXT_INVERSE,
        icon_color=colors.TEXT_INVERSE,
        text_style=typography.text_style("label", color=colors.TEXT_INVERSE),
        side=ft.BorderSide(1, colors.PRIMARY),
        padding=ft.Padding(16, 10, 16, 10),
        shape=_button_shape(radius.BUTTON),
        elevation=0,
        overlay_color=colors.PRIMARY_OVERLAY_STRONG,
    )


def _icon_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=colors.SURFACE,
        icon_color=colors.TEXT,
        side=ft.BorderSide(1, colors.OUTLINE),
        shape=_button_shape(radius.BUTTON),
        elevation=0,
        padding=ft.Padding(0, 0, 0, 0),
        overlay_color=colors.PRIMARY_OVERLAY,
    )


def _outlined_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=colors.SURFACE,
        color=colors.TEXT,
        icon_color=colors.TEXT,
        text_style=typography.text_style("label"),
        side=ft.BorderSide(1, colors.OUTLINE_STRONG),
        padding=ft.Padding(16, 10, 16, 10),
        shape=_button_shape(radius.BUTTON),
        elevation=0,
        overlay_color=colors.PRIMARY_OVERLAY_SOFT,
    )


def _text_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        color=colors.PRIMARY,
        icon_color=colors.PRIMARY,
        text_style=typography.text_style("label", color=colors.PRIMARY),
        padding=ft.Padding(12, 8, 12, 8),
        shape=_button_shape(radius.BUTTON),
        overlay_color=colors.PRIMARY_OVERLAY,
    )


def _card_theme() -> ft.CardTheme:
    return ft.CardTheme(
        color=colors.SURFACE,
        shadow_color=colors.SHADOW_STRONG,
        elevation=0,
        shape=_button_shape(radius.PANEL),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        margin=0,
    )


def _progress_indicator_theme() -> ft.ProgressIndicatorTheme:
    return ft.ProgressIndicatorTheme(
        color=colors.PRIMARY,
        circular_track_color=colors.PRIMARY_BORDER,
        linear_track_color=colors.PRIMARY_BORDER,
        border_radius=radius.FULL,
        track_gap=0,
        circular_track_padding=2,
        stroke_cap=ft.StrokeCap.ROUND,
        stroke_width=6,
        year_2023=False,
    )


def _slider_theme() -> ft.SliderTheme:
    return ft.SliderTheme(
        active_track_color=colors.PRIMARY,
        inactive_track_color=colors.PRIMARY_BORDER,
        active_tick_mark_color=colors.PRIMARY_BORDER,
        inactive_tick_mark_color=colors.PRIMARY_BORDER,
        disabled_active_track_color=colors.OUTLINE_STRONG,
        disabled_inactive_track_color=colors.OUTLINE,
        disabled_thumb_color=colors.OUTLINE_STRONG,
        thumb_color=colors.PRIMARY,
        overlay_color=colors.PRIMARY_OVERLAY,
        value_indicator_color=colors.PRIMARY_DARK,
        value_indicator_stroke_color=colors.PRIMARY_DARK,
        value_indicator_text_style=typography.text_style(
            "caption", color=colors.TEXT_INVERSE
        ),
        track_height=3,
        track_gap=0,
        thumb_size=ft.Size(18, 18),
        year_2023=False,
    )


def _popup_menu_theme() -> ft.PopupMenuTheme:
    return ft.PopupMenuTheme(
        color=colors.SURFACE,
        shadow_color=colors.SHADOW_STRONG,
        icon_color=colors.TEXT,
        label_text_style=typography.text_style("body"),
        elevation=0,
        shape=_button_shape(radius.PANEL),
        menu_padding=8,
    )


def _tooltip_theme() -> ft.TooltipTheme:
    return ft.TooltipTheme(
        wait_duration=animation.TOOLTIP_WAIT_DURATION_MS,
        show_duration=animation.TOOLTIP_SHOW_DURATION_MS,
        prefer_below=False,
        vertical_offset=20,
        padding=ft.Padding(10, 6, 10, 6),
        text_style=typography.text_style("caption", color=colors.TEXT_INVERSE),
        decoration=ft.BoxDecoration(
            bgcolor=colors.PRIMARY_DARK,
            border_radius=radius.SM,
        ),
    )


def _scrollbar_theme() -> ft.ScrollbarTheme:
    return ft.ScrollbarTheme(
        thumb_visibility=True,
        track_visibility=False,
        thickness=8,
        radius=radius.FULL,
        thumb_color=colors.PRIMARY,
        track_color=colors.PRIMARY_SOFT,
        track_border_color=colors.PRIMARY_BORDER,
        cross_axis_margin=2,
        main_axis_margin=2,
        min_thumb_length=42,
        interactive=True,
    )


def build_theme() -> ft.Theme:
    return ft.Theme(
        font_family=typography.FONT_FAMILY,
        use_material3=True,
        color_scheme=_color_scheme(),
        scaffold_bgcolor=colors.APP_BACKGROUND,
        card_bgcolor=colors.SURFACE,
        divider_color=colors.OUTLINE,
        splash_color=colors.PRIMARY_OVERLAY_STRONG,
        hover_color=colors.PRIMARY_OVERLAY_SOFT,
        highlight_color=colors.PRIMARY_OVERLAY_STRONG,
        focus_color=colors.PRIMARY_OVERLAY_STRONG,
        text_theme=_text_theme(),
        card_theme=_card_theme(),
        progress_indicator_theme=_progress_indicator_theme(),
        slider_theme=_slider_theme(),
        filled_button_theme=ft.FilledButtonTheme(style=_filled_button_style()),
        icon_button_theme=ft.IconButtonTheme(style=_icon_button_style()),
        outlined_button_theme=ft.OutlinedButtonTheme(style=_outlined_button_style()),
        text_button_theme=ft.TextButtonTheme(style=_text_button_style()),
        popup_menu_theme=_popup_menu_theme(),
        tooltip_theme=_tooltip_theme(),
        scrollbar_theme=_scrollbar_theme(),
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
