import asyncio
import logging

import flet as ft

from components.shell.activity_boundary import ActivityBoundary
from components.shell.app_body import AppBody
from components.shell.layout import Layout
from components.shell.loading_spinner import LoadingSpinner
from contexts.locale import LocaleContext, LocaleContextValue
from contexts.route import RouteContext, RouteContextValue
from models.app_model import AppModel
from theme.builder import configure_page

logger = logging.getLogger(__name__)


@ft.component
def App() -> ft.Control:
    app: AppModel
    app, _ = ft.use_state(lambda: AppModel(route=ft.context.page.route))  # type: ignore
    viewport_size, set_viewport_size = ft.use_state((0.0, 0.0))
    ui_ready, set_ui_ready = ft.use_state(False)
    entry_animation_started, set_entry_animation_started = ft.use_state(False)
    entry_animation_done, set_entry_animation_done = ft.use_state(False)

    _ = app.locale_version
    _ = app.route
    _ = viewport_size

    ft.context.page.on_route_change = app.route_change
    ft.context.page.on_view_pop = app.view_popped

    navigate_callback = ft.use_callback(
        lambda new_route: app.navigate(new_route), dependencies=[app.route]
    )
    route_value = ft.use_memo(
        lambda: RouteContextValue(
            route=app.route,
            navigate=navigate_callback,
        ),
        dependencies=[app.route],
    )

    set_locale = ft.use_callback(
        lambda loc: app.set_locale(loc), dependencies=[app.locale_version]
    )
    locale_value = ft.use_memo(
        lambda: LocaleContextValue(
            locale=app.locale,
            translations=app.translations,
            set_locale=set_locale,
        ),
        dependencies=[app.locale_version, set_locale],
    )

    async def monitor_loop() -> None:
        logger.info("Global inactivity monitor task started")
        while True:
            await asyncio.sleep(1.0)
            app.check_inactivity()
            app.sync_motor_state()

    async def initialize_motors_task() -> None:
        await asyncio.to_thread(app.initialize_motors)

    async def shutdown_motors_task() -> None:
        await asyncio.to_thread(app.shutdown_motors)

    def get_current_viewport_size() -> tuple[float, float]:
        return (
            float(getattr(ft.context.page, "width", 0) or 0),
            float(getattr(ft.context.page, "height", 0) or 0),
        )

    def sync_viewport_size(*, force: bool = False) -> None:
        size = get_current_viewport_size()
        previous = getattr(ft.context.page, "_last_synced_viewport_size", None)
        if not force and previous == size:
            return
        setattr(ft.context.page, "_last_synced_viewport_size", size)
        set_viewport_size(size)

    async def wait_for_viewport_stable(
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
            current = get_current_viewport_size()
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

    async def warmup_first_frame_update_task() -> None:
        logger.info("Viewport warmup started")
        try:
            stable_before = await wait_for_viewport_stable()
            if not stable_before:
                width, height = get_current_viewport_size()
                logger.info(
                    "Viewport warmup pre-update timed out at %.0fx%.0f",
                    width,
                    height,
                )

            ft.context.page.update()

            stable_after = await wait_for_viewport_stable(
                timeout_s=0.8, stable_samples=2
            )
            sync_viewport_size()
            width, height = get_current_viewport_size()
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
            set_ui_ready(True)

    async def complete_entry_animation_task() -> None:
        await asyncio.sleep(0.28)
        set_entry_animation_done(True)

    def on_page_resize(_: object) -> None:
        sync_viewport_size()

    def build_app_shell(*, key: str | None = None) -> ft.Container:
        return ft.Container(
            key=key,
            expand=True,
            content=ActivityBoundary(
                on_activity=app.reset_timer,
                content=Layout(app, AppBody(app)),
            ),
        )

    def build_loading_shell() -> ft.Container:
        return ft.Container(
            key="app-loading-shell",
            expand=True,
            content=LoadingSpinner(size=56),
        )

    def on_mounted() -> None:
        ft.context.page.title = "Tango Motors Control"
        ft.context.page.window.maximized = True
        ft.context.page.window.full_screen = True
        ft.context.page.window.frameless = True
        configure_page(ft.context.page)
        ft.context.page.on_resize = on_page_resize
        sync_viewport_size(force=True)
        ft.context.page.on_keyboard_event = lambda _: app.reset_timer()
        ft.context.page.run_task(initialize_motors_task)
        ft.context.page.run_task(monitor_loop)
        ft.context.page.run_task(warmup_first_frame_update_task)

    ft.on_mounted(on_mounted)
    ft.on_unmounted(shutdown_motors_task)

    def on_ui_ready_changed() -> None:
        if ui_ready and not entry_animation_started and not entry_animation_done:
            set_entry_animation_started(True)
            ft.context.page.run_task(complete_entry_animation_task)

    ft.on_updated(on_ui_ready_changed, [ui_ready])

    return LocaleContext(
        locale_value,
        lambda: RouteContext(
            route_value,
            lambda: ft.View(
                route="/",
                padding=0,
                controls=[
                    (
                        build_app_shell()
                        if entry_animation_done
                        else ft.AnimatedSwitcher(
                            expand=True,
                            transition=ft.AnimatedSwitcherTransition.FADE,
                            duration=240,
                            reverse_duration=0,
                            content=(
                                build_app_shell(key="app-ready")
                                if ui_ready
                                else build_loading_shell()
                            ),
                        )
                    )
                ],
            ),
        ),
    )
