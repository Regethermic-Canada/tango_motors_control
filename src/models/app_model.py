import time
import logging
from dataclasses import dataclass, field
import flet as ft
from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


@ft.observable  # pyright: ignore[reportUnknownMemberType]
@dataclass
class AppModel:
    route: str = "/"
    counter_val: int = 0
    theme_mode: ft.ThemeMode = ft.ThemeMode.DARK
    last_interaction: float = field(default_factory=time.time)
    is_screensaver_active: bool = False
    inactivity_limit: float = 30.0

    def __post_init__(self) -> None:
        self.inactivity_limit = config.inactivity_timeout

        saved_theme = config.theme_mode
        self.theme_mode = (
            ft.ThemeMode.LIGHT if saved_theme == "LIGHT" else ft.ThemeMode.DARK
        )

        logger.info(
            f"App initialized. Theme: {self.theme_mode}, Timeout: {self.inactivity_limit}s"
        )

    def navigate(self, new_route: str) -> None:
        if self.route != new_route:
            self.route = new_route
            logger.info(f"Navigating to {new_route}")

    def increment(self) -> None:
        self.counter_val += 1
        self.reset_timer()
        logger.info(f"Counter incremented to {self.counter_val}")

    def decrement(self) -> None:
        self.counter_val -= 1
        self.reset_timer()
        logger.info(f"Counter decremented to {self.counter_val}")

    def toggle_theme(self) -> None:
        self.theme_mode = (
            ft.ThemeMode.LIGHT
            if self.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        config_value = "LIGHT" if self.theme_mode == ft.ThemeMode.LIGHT else "DARK"
        config.set("THEME_MODE", config_value)

        self.reset_timer()
        logger.info(f"Theme toggled to {self.theme_mode}")

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
