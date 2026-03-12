import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import flet as ft

from services.motors.motor_service import MotorService, MotorServiceConfig
from utils.config import config

logger: logging.Logger = logging.getLogger(__name__)


class MotorAction(Enum):
    STARTED = "started"
    STOPPED = "stopped"
    START_FAILED_NO_MOTORS = "start_failed_no_motors"
    START_FAILED = "start_failed"
    STOP_FAILED = "stop_failed"


@dataclass(frozen=True)
class MotorActionResult:
    action: MotorAction
    error: str = ""


@ft.observable
class AppModel:
    def __init__(self, route: str = "/"):
        self.route = route
        self.speed_min = -10
        self.speed_max = 10
        self.speed_level = 0
        self.speed_percent = 0
        self.speed_percent_max = 100
        self.is_motors_running = False
        self._motors_armed = False
        self.locale = "en"
        self.locale_version = 0
        self.default_translations: dict[str, str] = {}
        self.translations: dict[str, str] = {}
        self.last_interaction = time.time()
        self.is_screensaver_active = False
        self.inactivity_limit = 30.0

        # Load persisted preferences
        self.inactivity_limit = config.inactivity_timeout
        self.default_translations = self._read_translations_file("en")
        self.locale = config.locale
        self.translations = self._build_translations(self.locale)
        self.speed_max = abs(config.motor_max_step_speed)
        self.speed_min = -self.speed_max
        self.speed_percent_max = min(100, abs(config.motor_max_speed))
        self.speed_level = self._clamp_speed(config.default_speed)
        self.speed_percent = self._level_to_percent(self.speed_level)
        self._motor_service = MotorService(MotorServiceConfig.from_app_config(config))

        logger.info(
            f"App Refreshed. Locale: {self.locale}, Timeout: {self.inactivity_limit}s"
        )

    def _read_translations_file(self, locale: str) -> dict[str, str]:
        project_root: Path = Path(__file__).resolve().parent.parent
        lang_file = project_root / "assets" / "lang" / f"{locale}.json"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {
                    str(key): str(value)
                    for key, value in data.items()
                    if isinstance(key, str) and isinstance(value, str)
                }

        logger.error(f"Translation file not found: {lang_file}")
        return {}

    def _build_translations(self, locale: str) -> dict[str, str]:
        if locale == "en":
            return dict(self.default_translations)

        translations = dict(self.default_translations)
        translations.update(self._read_translations_file(locale))
        return translations

    def set_locale(self, locale: str) -> None:
        if self.locale != locale:
            self.locale = locale
            self.translations = self._build_translations(locale)
            self.locale_version += 1
            config.set("LOCALE", locale)
            logger.info(f"Locale changed to {self.locale}")

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        logger.info(f"Route changed from: {self.route} to: {e.route}")
        self.route = e.route

    def navigate(self, new_route: str) -> None:
        if new_route != self.route:
            logger.info(f"Navigating to: {new_route}")
            asyncio.create_task(ft.context.page.push_route(new_route))

    async def view_popped(self, e: ft.ViewPopEvent) -> None:
        logger.info("View popped")
        views = ft.unwrap_component(ft.context.page.views)
        if len(views) > 1:
            await ft.context.page.push_route(views[-2].route)

    def increment(self) -> bool:
        previous_speed = self.speed_level
        self.speed_level = self._clamp_speed(self.speed_level + 1)
        if self.speed_level == previous_speed:
            return False
        self._apply_speed_to_motors()
        logger.info(
            "Speed level incremented to %s (target=%s%%)",
            self.speed_level,
            self.speed_percent,
        )
        return True

    def decrement(self) -> bool:
        previous_speed = self.speed_level
        self.speed_level = self._clamp_speed(self.speed_level - 1)
        if self.speed_level == previous_speed:
            return False
        self._apply_speed_to_motors()
        logger.info(
            "Speed level decremented to %s (target=%s%%)",
            self.speed_level,
            self.speed_percent,
        )
        return True

    def can_increment(self) -> bool:
        return self.speed_level < max(self.speed_min, self.speed_max)

    def can_decrement(self) -> bool:
        return self.speed_level > min(self.speed_min, self.speed_max)

    def set_inactivity_timeout(self, seconds: float) -> None:
        if self.inactivity_limit != seconds:
            self.inactivity_limit = seconds
            config.set("INACTIVITY_TIMEOUT", seconds)
            logger.info(f"Inactivity timeout changed to {self.inactivity_limit}s")

    def update_admin_passcode(self, new_passcode: str) -> None:
        from argon2 import PasswordHasher

        ph = PasswordHasher()
        new_hash = ph.hash(new_passcode)
        config.set("ADMIN_PASSCODE_HASH", new_hash)
        logger.info("Admin passcode updated and persisted.")

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

    def sync_motor_state(self) -> None:
        running = self._motor_service.is_running()
        if running != self.is_motors_running:
            self.is_motors_running = running
            logger.info("Motor running state changed to %s", self.is_motors_running)

    def initialize_motors(self) -> None:
        try:
            self._motor_service.initialize()
        except Exception:
            logger.exception("Motor CAN initialization failed")

    def start_motors(self) -> MotorActionResult:
        try:
            self._motor_service.start(initial_speed_percent=self.speed_percent)
            self.is_motors_running = self._motor_service.is_running()
            if self.is_motors_running:
                self._motors_armed = True
                return MotorActionResult(action=MotorAction.STARTED)
            self._motors_armed = False
            return MotorActionResult(
                action=MotorAction.START_FAILED,
                error="Motor service did not enter running state",
            )
        except Exception as ex:
            self.is_motors_running = False
            self._motors_armed = False
            logger.exception("Motor startup failed")
            if "No configured motors are connected" in str(ex):
                return MotorActionResult(
                    action=MotorAction.START_FAILED_NO_MOTORS, error=str(ex)
                )
            return MotorActionResult(action=MotorAction.START_FAILED, error=str(ex))

    def stop_motors(self) -> MotorActionResult:
        try:
            self._motor_service.stop()
            self.is_motors_running = False
            self._motors_armed = False
            return MotorActionResult(action=MotorAction.STOPPED)
        except Exception as ex:
            logger.exception("Motor shutdown failed")
            return MotorActionResult(action=MotorAction.STOP_FAILED, error=str(ex))

    def shutdown_motors(self) -> None:
        try:
            self._motor_service.shutdown()
            self.is_motors_running = False
            self._motors_armed = False
        except Exception:
            logger.exception("Motor full shutdown failed")

    def rescan_motors(self) -> bool:
        try:
            running = self._motor_service.rescan()
            self.is_motors_running = running
            return True
        except Exception:
            logger.exception("Motor rescan failed")
            self.is_motors_running = self._motor_service.is_running()
            return False

    def toggle_motors(self) -> MotorActionResult:
        if self.is_motors_running:
            result = self.stop_motors()
        else:
            result = self.start_motors()
        return result

    def _apply_speed_to_motors(self) -> None:
        try:
            target_percent = self._level_to_percent(self.speed_level)

            if target_percent == 0:
                self.speed_percent = 0
                if self.is_motors_running:
                    self._motor_service.stop()
                    self.is_motors_running = False
                    logger.info("Speed reached 0%%; motors auto-stopped")
                return

            self.speed_percent = target_percent
            if not self.is_motors_running and self._motors_armed:
                self._motor_service.start(initial_speed_percent=target_percent)
                self.is_motors_running = self._motor_service.is_running()
                if self.is_motors_running:
                    logger.info(
                        "Speed left 0%% while armed; motors auto-started at %s%%",
                        target_percent,
                    )

            if self.is_motors_running:
                self.speed_percent = self._motor_service.set_speed_percent(
                    target_percent
                )
        except Exception:
            logger.exception("Failed to apply speed command to motors")

    def _clamp_speed(self, speed: int) -> int:
        low = min(self.speed_min, self.speed_max)
        high = max(self.speed_min, self.speed_max)
        return max(low, min(speed, high))

    def _level_to_percent(self, level: int) -> int:
        level = self._clamp_speed(level)
        if level == 0 or self.speed_max <= 0 or self.speed_percent_max <= 0:
            return 0

        return int(round((level / self.speed_max) * self.speed_percent_max))
