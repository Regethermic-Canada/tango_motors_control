import asyncio
import logging

import flet as ft

from components.speed_view import SpeedView
from components.navigation import (
    LanguageSelector,
    ThemeModeToggle,
    ThemeSeedColor,
    AdminModeToggle,
)
from components.screensaver import Screensaver
from models.app_model import AppModel
from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


@ft.component
def MainView(app_model: AppModel) -> ft.Control:
    ASSET_LOGO: str = config.asset_logo
    ASSET_SCREENSAVER: str = config.asset_screensaver

    async def monitor_loop() -> None:
        logger.info("Inactivity monitor task started")
        while True:
            await asyncio.sleep(1.0)
            app_model.check_inactivity()

    def on_mounted() -> None:
        ft.context.page.on_pointer_down = lambda _: app_model.reset_timer()  # type: ignore[attr-defined]
        ft.context.page.on_keyboard_event = lambda _: app_model.reset_timer()
        ft.context.page.run_task(monitor_loop)

    ft.on_mounted(on_mounted)

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
                # 2. Main Content Layer
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=SpeedView(app_model),
                ),
                # 3. Header Layer (Theme Controls)
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
                # 4. Screensaver Overlay
                *(
                    [
                        Screensaver(
                            asset_path=ASSET_SCREENSAVER,
                            on_click=lambda _: app_model.reset_timer(),
                        )
                    ]
                    if app_model.is_screensaver_active
                    else []
                ),
            ],
        ),
    )
