import asyncio
import logging

import flet as ft

from components.counter_view import CounterView
from components.screensaver import Screensaver
from contexts.theme import ThemeContext
from models.app_model import AppModel
from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


@ft.component
def MainView(app_model: AppModel) -> ft.Control:
    theme = ft.use_context(ThemeContext)

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

    def seed_color_item(color: ft.Colors, name: str) -> ft.PopupMenuItem:
        display_name = f"{name} (default)" if color == app_model.theme_color else name
        return ft.PopupMenuItem(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=color),
                    ft.Text(display_name),
                ],
            ),
            on_click=lambda _: theme.set_seed_color(color),
        )

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
                    content=CounterView(app_model),
                ),
                # 3. Header Layer (Theme Controls)
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.PopupMenuButton(
                                icon=ft.Icons.COLOR_LENS_OUTLINED,
                                tooltip="Select theme seed color",
                                items=[
                                    seed_color_item(
                                        ft.Colors.DEEP_PURPLE, "Deep purple"
                                    ),
                                    seed_color_item(ft.Colors.INDIGO, "Indigo"),
                                    seed_color_item(ft.Colors.BLUE, "Blue"),
                                    seed_color_item(ft.Colors.TEAL, "Teal"),
                                    seed_color_item(ft.Colors.GREEN, "Green"),
                                    seed_color_item(ft.Colors.YELLOW, "Yellow"),
                                    seed_color_item(ft.Colors.ORANGE, "Orange"),
                                    seed_color_item(
                                        ft.Colors.DEEP_ORANGE, "Deep orange"
                                    ),
                                    seed_color_item(ft.Colors.PINK, "Pink"),
                                ],
                            ),
                            ft.IconButton(
                                icon=(
                                    ft.Icons.DARK_MODE
                                    if app_model.theme_mode == ft.ThemeMode.DARK
                                    else ft.Icons.LIGHT_MODE
                                ),
                                on_click=lambda _: theme.toggle_mode(),
                                tooltip="Toggle Theme",
                                key="theme_toggle_btn",
                            ),
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
