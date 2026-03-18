import asyncio
import logging
from collections.abc import Callable

import flet as ft

from services.motors.controller import MotorController
from .settings import SettingsService
from .shell import ShellService
from theme.builder import configure_page
from utils.config import config

logger = logging.getLogger(__name__)


class AppRuntime:
    def __init__(
        self,
        *,
        page: ft.Page,
        motor_controller: MotorController,
        settings_service: SettingsService,
        shell_service: ShellService,
        set_viewport_size: Callable[[tuple[float, float]], None],
        set_ui_ready: Callable[[bool], None],
    ) -> None:
        self._page = page
        self._motor_controller = motor_controller
        self._settings_service = settings_service
        self._shell_service = shell_service
        self._set_viewport_size = set_viewport_size
        self._set_ui_ready = set_ui_ready

    async def monitor_loop(self) -> None:
        logger.info("Global inactivity monitor task started")
        while True:
            await asyncio.sleep(1.0)
            self._shell_service.check_inactivity(
                self._settings_service.inactivity_timeout
            )

            # If screensaver is active, ensure overlays are closed
            if self._shell_service.is_screensaver_active:
                self._close_all_overlays()

            self._motor_controller.sync_motor_state()

    def _close_all_overlays(self) -> None:
        """Closes all active sheets, dialogs, and banners in the page overlay."""
        # Explicitly set open=False on all supported controls in the overlay
        for control in self._page.overlay:
            if hasattr(control, "open"):
                control.open = False

        # Also use the official close method if available for standard dialogs
        if hasattr(self._page, "close"):
            try:
                self._page.close()
            except Exception:
                pass

        self._page.update()

    async def initialize_motors_task(self) -> None:
        await asyncio.to_thread(self._motor_controller.initialize_motors)

    async def shutdown_motors_task(self) -> None:
        await asyncio.to_thread(self._motor_controller.shutdown_motors)

    def on_page_resize(self, _: object) -> None:
        self.sync_viewport_size()

    def on_mounted(self) -> None:
        self._page.title = config.app_title
        self._page.window.maximized = True
        self._page.window.full_screen = True
        self._page.window.frameless = True
        configure_page(self._page)
        self._page.on_resize = self.on_page_resize
        self.sync_viewport_size(force=True)
        self._page.on_keyboard_event = lambda _: self._shell_service.reset_timer()
        self._page.run_task(self.initialize_motors_task)
        self._page.run_task(self.monitor_loop)
        self._page.run_task(self.warmup_first_frame_update_task)

    async def on_unmounted(self) -> None:
        await self.shutdown_motors_task()

    def sync_viewport_size(self, *, force: bool = False) -> None:
        size = self._get_current_viewport_size()
        previous = getattr(self._page, "_last_synced_viewport_size", None)
        if not force and previous == size:
            return

        setattr(self._page, "_last_synced_viewport_size", size)
        self._set_viewport_size(size)

    def _get_current_viewport_size(self) -> tuple[float, float]:
        return (
            float(getattr(self._page, "width", 0) or 0),
            float(getattr(self._page, "height", 0) or 0),
        )

    async def _wait_for_viewport_stable(
        self,
        *,
        timeout_s: float = 2.0,
        poll_s: float = 0.12,
        stable_samples: int = 3,
    ) -> bool:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_s
        previous: tuple[float, float] | None = None
        stable_count = 0

        while True:
            current = self._get_current_viewport_size()
            if (
                previous is not None
                and current != (0.0, 0.0)
                and abs(current[0] - previous[0]) < 0.5
                and abs(current[1] - previous[1]) < 0.5
            ):
                stable_count += 1
            else:
                stable_count = 0

            previous = current
            if stable_count >= stable_samples:
                return True
            if loop.time() >= deadline:
                return False
            await asyncio.sleep(poll_s)

    async def warmup_first_frame_update_task(self) -> None:
        logger.info("Viewport warmup started")
        try:
            stable_before = await self._wait_for_viewport_stable()
            if not stable_before:
                width, height = self._get_current_viewport_size()
                logger.info(
                    "Viewport warmup pre-update timed out at %.0fx%.0f",
                    width,
                    height,
                )

            self._page.update()

            stable_after = await self._wait_for_viewport_stable(
                timeout_s=0.8,
                stable_samples=2,
            )
            self.sync_viewport_size()
            width, height = self._get_current_viewport_size()
            logger.info(
                "Viewport warmup completed (pre_stable=%s, post_stable=%s, size=%.0fx%.0f)",
                stable_before,
                stable_after,
                width,
                height,
            )
        except Exception:
            logger.exception("Viewport warmup failed")
        finally:
            self._set_ui_ready(True)
