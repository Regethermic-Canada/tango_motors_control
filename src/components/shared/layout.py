import flet as ft
from models.app_model import AppModel
from utils.ui_scale import get_viewport_metrics
from .navigation import (
    LanguageSelector,
    ThemeModeToggle,
    ThemeSeedColor,
    AdminModeToggle,
)
from .screensaver import Screensaver
from utils.config import config


@ft.component
def Layout(app_model: AppModel, content: ft.Control) -> ft.Control:
    ASSET_LOGO = config.asset_logo
    ASSET_SCREENSAVER = config.asset_screensaver
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    logo_bottom_padding = int(round(60 * metrics.scale))
    logo_width = int(round((280 if metrics.compact else 400) * metrics.scale))
    header_top = int(round(20 * metrics.scale))
    header_right = int(round(20 * metrics.scale))

    return ft.Container(
        expand=True,
        bgcolor=f"{app_model.theme_color.value},0.04",
        content=ft.Stack(
            expand=True,
            controls=[
                # 1. Background Layer (Logo)
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.BOTTOM_CENTER,
                    padding=ft.Padding(0, 0, 0, logo_bottom_padding),
                    opacity=0.1,
                    content=ft.Image(
                        src=ASSET_LOGO,
                        width=logo_width,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                ),
                # 2. Page Content
                ft.Container(
                    expand=True,
                    content=content,
                ),
                # 3. Global Header
                ft.Container(
                    content=ft.Row(
                        controls=[
                            AdminModeToggle(app_model),
                            LanguageSelector(),
                            ThemeSeedColor(),
                            ThemeModeToggle(),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    top=header_top,
                    right=header_right,
                ),
                # 4. Global Screensaver Overlay
                *(
                    [Screensaver(ASSET_SCREENSAVER, lambda _: app_model.reset_timer())]
                    if app_model.is_screensaver_active
                    else []
                ),
            ],
        ),
    )
