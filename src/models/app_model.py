import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import flet as ft

from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


@ft.observable
@dataclass
class AppModel:
    route: str = "/"
    speed_level: int = 0
    theme_mode: ft.ThemeMode = ft.ThemeMode.DARK
    theme_color: ft.Colors = ft.Colors.BLUE
    locale: str = "en"
    translations: dict[str, str] = field(default_factory=dict)
    last_interaction: float = field(default_factory=time.time)
    is_screensaver_active: bool = False
    inactivity_limit: float = 30.0

    def __post_init__(self) -> None:
        self.inactivity_limit = config.inactivity_timeout

        # Load persisted preferences
        saved_mode = config.theme_mode
        self.theme_mode = (
            ft.ThemeMode.LIGHT if saved_mode == "LIGHT" else ft.ThemeMode.DARK
        )

        saved_color_name = config.theme_color.lower()
        try:
            self.theme_color = getattr(ft.Colors, saved_color_name.upper())
        except AttributeError:
            self.theme_color = ft.Colors.BLUE

        self.locale = config.locale
        self.load_translations()

        logger.info(
            f"App Refreshed. Theme: {self.theme_mode}, Color: {self.theme_color}, Locale: {self.locale}, Timeout: {self.inactivity_limit}s"
        )

    def load_translations(self) -> None:
        project_root: Path = Path(__file__).resolve().parent.parent
        lang_file = project_root / "assets" / "lang" / f"{self.locale}.json"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        else:
            logger.error(f"Translation file not found: {lang_file}")
            self.translations = {}

    def set_locale(self, locale: str) -> None:
        if self.locale != locale:
            self.locale = locale
            config.set("LOCALE", locale)
            self.load_translations()
            self.reset_timer()
            logger.info(f"Locale changed to {self.locale}")

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        logger.info(f"Route changed from: {self.route} to: {e.route}")
        self.route = e.route
        self.reset_timer()

    def navigate(self, new_route: str) -> None:
        if new_route != self.route:
            logger.info(f"Navigating to: {new_route}")
            asyncio.create_task(ft.context.page.push_route(new_route))

    async def view_popped(self, e: ft.ViewPopEvent) -> None:
        logger.info("View popped")
        views = ft.unwrap_component(ft.context.page.views)
        if len(views) > 1:
            await ft.context.page.push_route(views[-2].route)

    def increment(self) -> None:
        self.speed_level += 1
        self.reset_timer()
        logger.info(f"Speed level incremented to {self.speed_level}")

    def decrement(self) -> None:
        self.speed_level -= 1
        self.reset_timer()
        logger.info(f"Speed level decremented to {self.speed_level}")

    def toggle_theme(self) -> None:
        self.theme_mode = (
            ft.ThemeMode.DARK
            if self.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        config_value = "LIGHT" if self.theme_mode == ft.ThemeMode.LIGHT else "DARK"
        config.set("THEME_MODE", config_value)
        self.reset_timer()
        logger.info(f"Theme toggled to {self.theme_mode}")

    def set_theme_color(self, color: ft.Colors) -> None:
        self.theme_color = color
        # Persist color name (e.g. 'blue', 'deep_orange')
        color_name = color.name if hasattr(color, "name") else str(color)
        config.set("THEME_COLOR", color_name.upper())
        self.reset_timer()
        logger.info(f"Theme color changed to {self.theme_color}")

    def reset_timer(self) -> None:
        self.last_interaction = time.time()
        if self.is_screensaver_active:
            self.is_screensaver_active = False
            logger.info("Screensaver dismissed")

    def check_inactivity(self) -> None:
        elapsed: float = time.time() - self.last_interaction
        if elapsed > self.inactivity_limit and not self.is_screensaver_active:
            self.is_screensaver_active = True
            logger.info("Screensaver activated due to inactivity")
