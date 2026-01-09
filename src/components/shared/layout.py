import flet as ft
from models.app_model import AppModel
from .navigation import LanguageSelector, ThemeModeToggle, ThemeSeedColor, AdminModeToggle
from .screensaver import Screensaver
from utils.config import config

@ft.component
def Layout(app_model: AppModel, content: ft.Control) -> ft.Control:
    ASSET_LOGO = config.asset_logo
    ASSET_SCREENSAVER = config.asset_screensaver

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
                    padding=ft.Padding(0, 0, 0, 60),
                    opacity=0.1,
                    content=ft.Image(src=ASSET_LOGO, width=400, fit=ft.BoxFit.CONTAIN),
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
                    top=20,
                    right=20,
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