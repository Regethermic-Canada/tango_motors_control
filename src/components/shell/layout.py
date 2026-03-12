import flet as ft
from components.native.card import TangoCard
from models.app_model import AppModel
from theme import colors, radius, spacing
from theme.scale import get_viewport_metrics
from .navigation import AdminModeToggle, LanguageSelector
from .screensaver import Screensaver
from utils.config import config


@ft.component
def Layout(app_model: AppModel, content: ft.Control) -> ft.Control:
    ASSET_LOGO = config.asset_logo
    ASSET_SCREENSAVER = config.asset_screensaver
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    logo_bottom_padding = int(round((spacing.XL + spacing.XS) * metrics.scale))
    logo_width = int(round((240 if metrics.compact else 320) * metrics.scale))
    header_top = int(round(spacing.XS * metrics.scale))
    header_right = int(round(spacing.MD * metrics.scale))
    header_gap = int(round(spacing.XS * metrics.scale))
    header_card_padding = int(round(4 * metrics.scale))
    top_band_height = int(round((68 if metrics.compact else 76) * metrics.scale))
    toast_top_offset = top_band_height + int(round(spacing.SM * metrics.scale))

    setattr(ft.context.page, "_tango_toast_top_offset", toast_top_offset)
    setattr(ft.context.page, "_tango_toast_right_offset", header_right)

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
                    content=content,
                ),
                ft.Container(
                    top=header_top,
                    right=header_right,
                    content=TangoCard(
                        padding=ft.Padding(
                            header_card_padding,
                            header_card_padding,
                            header_card_padding,
                            header_card_padding,
                        ),
                        border_radius=radius.SHELL,
                        content=ft.Row(
                            controls=[
                                AdminModeToggle(app_model),
                                LanguageSelector(),
                            ],
                            spacing=header_gap,
                            tight=True,
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ),
                ),
                *(
                    [Screensaver(ASSET_SCREENSAVER, lambda _: app_model.reset_timer())]
                    if app_model.is_screensaver_active
                    else []
                ),
            ],
        ),
    )
