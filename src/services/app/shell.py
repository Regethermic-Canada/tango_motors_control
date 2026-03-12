import logging
import time

import flet as ft

logger = logging.getLogger(__name__)


@ft.observable
class ShellService:
    def __init__(self) -> None:
        self.last_interaction = time.time()
        self.is_screensaver_active = False

    def reset_timer(self) -> None:
        self.last_interaction = time.time()
        if self.is_screensaver_active:
            self.is_screensaver_active = False
            logger.info("Screensaver dismissed")

    def check_inactivity(self, inactivity_timeout: float) -> None:
        elapsed = time.time() - self.last_interaction
        if elapsed > inactivity_timeout and not self.is_screensaver_active:
            self.is_screensaver_active = True
            logger.info("Screensaver activated due to inactivity")
