import flet as ft
from components.ui.text import TangoText
from contexts.locale import LocaleContext
from contexts.route import RouteContext
from contexts.shell import ShellContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics
from .navigation import AdminModeToggle, LanguageSelector
from .screensaver import Screensaver
from utils.config import config


@ft.component
def Layout(content: ft.Control) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    route_ctx = ft.use_context(RouteContext)
    shell = ft.use_context(ShellContext).current()
    ASSET_LOGO = config.asset_logo
    ASSET_SCREENSAVER = config.asset_screensaver
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    logo_bottom_padding = int(round((spacing.XL + spacing.XS) * metrics.scale))
    body_bottom_inset = int(round((spacing.XXL + spacing.SM) * metrics.scale))
    logo_width = int(round((240 if metrics.is_compact else 320) * metrics.scale))
    header_side_padding = int(
        round((spacing.MD if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    header_right = int(round(spacing.MD * metrics.scale))
    header_gap = int(round((spacing.XS if metrics.is_compact else spacing.SM) * metrics.scale))
    top_band_height = int(round((68 if metrics.is_compact else 76) * metrics.scale))
    toast_top_offset = top_band_height + int(round(spacing.SM * metrics.scale))
    title_spacing = int(round(2 * metrics.scale))
    title_size = int(round((18 if metrics.is_compact else 22) * metrics.scale))
    subtitle_size = int(round((11 if metrics.is_compact else 13) * metrics.scale))

    setattr(ft.context.page, "_tango_toast_top_offset", toast_top_offset)
    setattr(ft.context.page, "_tango_toast_right_offset", header_right)
    setattr(ft.context.page, "_tango_toast_close_tooltip", loc.t("close"))
    setattr(ft.context.page, "_tango_content_top_inset", top_band_height)
    setattr(ft.context.page, "_tango_content_bottom_inset", body_bottom_inset)

    title_key = "motors_control"
    subtitle_key: str | None = None
    if route_ctx.route == "/auth":
        title_key = "admin_access"
        subtitle_key = "enter_passcode"
    elif route_ctx.route == "/admin":
        title_key = "admin_settings"
        subtitle_key = "application_config"

    title_block = ft.Column(
        spacing=title_spacing,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            TangoText(
                loc.t(title_key),
                variant="title",
                size=title_size,
                color=colors.TEXT_INVERSE,
            ),
            *(
                [
                    TangoText(
                        loc.t(subtitle_key),
                        variant="caption",
                        size=subtitle_size,
                        color=colors.APP_SHELL_SUBTITLE,
                    )
                ]
                if subtitle_key
                else []
            ),
        ],
    )

    return ft.Container(
        expand=True,
        bgcolor=colors.APP_BACKGROUND,
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    height=top_band_height,
                    expand=False,
                    bgcolor=colors.APP_SHELL,
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.BOTTOM_CENTER,
                    padding=ft.Padding(0, 0, 0, logo_bottom_padding),
                    opacity=0.08,
                    content=ft.Image(
                        src=ASSET_LOGO,
                        width=logo_width,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding(0, top_band_height, 0, body_bottom_inset),
                    content=content,
                ),
                ft.Container(
                    top=0,
                    left=0,
                    right=0,
                    height=top_band_height,
                    padding=ft.Padding(
                        header_side_padding,
                        0,
                        header_side_padding,
                        0,
                    ),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            title_block,
                            ft.Row(
                                controls=[
                                    AdminModeToggle(),
                                    LanguageSelector(),
                                ],
                                spacing=header_gap,
                                tight=True,
                                alignment=ft.MainAxisAlignment.END,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                    ),
                ),
                *(
                    [Screensaver(ASSET_SCREENSAVER)]
                    if shell.is_screensaver_active
                    else []
                ),
            ],
        ),
    )
