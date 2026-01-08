import time
import logging
import flet as ft
from models.app_model import AppModel
from components.counter_view import CounterView
from components.screensaver import Screensaver
from contexts.theme import ThemeContext, ThemeContextValue
from contexts.route import RouteContext, RouteContextValue
from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


@ft.component
def App() -> ft.Control:
    model: AppModel
    model, _ = (  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        ft.use_state(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            AppModel()
        )
    )

    ASSET_LOGO: str = config.asset_logo
    ASSET_SCREENSAVER: str = config.asset_screensaver

    def monitor_loop() -> None:
        logger.info("Inactivity monitor thread started")
        while True:
            time.sleep(1.0)
            model.check_inactivity()

    def on_mounted() -> None:
        ft.context.page.title = config.app_title
        ft.context.page.on_pointer_down = lambda _: model.reset_timer()  # type: ignore[attr-defined]
        ft.context.page.on_keyboard_event = lambda _: model.reset_timer()
        ft.context.page.run_thread(monitor_loop)

    ft.on_mounted(on_mounted)

    def update_theme() -> None:
        ft.context.page.theme_mode = model.theme_mode
        logger.debug(f"Applied theme mode: {model.theme_mode}")

    ft.on_updated(update_theme, [model.theme_mode])

    theme_value: ThemeContextValue = ft.use_memo(
        lambda: ThemeContextValue(
            mode=model.theme_mode,
            toggle_mode=lambda: model.toggle_theme(),
        ),
        dependencies=[model.theme_mode],
    )

    route_value: RouteContextValue = ft.use_memo(
        lambda: RouteContextValue(
            route=model.route,
            navigate=lambda r: model.navigate(r),
        ),
        dependencies=[model.route],
    )

    return RouteContext(
        route_value,
        lambda: ThemeContext(
            theme_value,
            lambda: ft.View(
                route="/",
                padding=0,
                controls=[
                    ft.Stack(
                        expand=True,
                        controls=[
                            # 1. Background Layer
                            ft.Container(
                                expand=True,
                                alignment=ft.Alignment.BOTTOM_CENTER,
                                padding=ft.Padding(0, 0, 0, 60),
                                opacity=0.1,
                                content=ft.Image(
                                    src=ASSET_LOGO, width=400, fit=ft.BoxFit.CONTAIN
                                ),
                            ),
                            # 2. Controls Layer
                            ft.Container(
                                expand=True,
                                alignment=ft.Alignment.CENTER,
                                content=CounterView(model),
                            ),
                            # 3. Header Layer
                            ft.Container(
                                content=ft.IconButton(
                                    icon=(
                                        ft.Icons.DARK_MODE
                                        if model.theme_mode == ft.ThemeMode.DARK
                                        else ft.Icons.LIGHT_MODE
                                    ),
                                    on_click=lambda _: model.toggle_theme(),
                                    tooltip="Toggle Theme",
                                ),
                                top=20,
                                right=20,
                            ),
                            # 4. Screensaver Overlay
                            (
                                Screensaver(
                                    asset_path=ASSET_SCREENSAVER,
                                    on_click=lambda _: model.reset_timer(),
                                )
                                if model.is_screensaver_active
                                else ft.Container(visible=False)
                            ),
                        ],
                    )
                ],
            ),
        ),
    )
