import asyncio
import logging
import flet as ft

from components.shared.layout import Layout
from components.shared.app_body import AppBody
from contexts.locale import LocaleContext, LocaleContextValue
from contexts.route import RouteContext, RouteContextValue
from contexts.theme import ThemeContext, ThemeContextValue
from models.app_model import AppModel

logger = logging.getLogger(__name__)


@ft.component
def App() -> ft.Control:
    # Use a lambda to ensure AppModel is only instantiated once
    app: AppModel
    app, _ = ft.use_state(lambda: AppModel(route=ft.context.page.route))  # type: ignore
    viewport_size, set_viewport_size = ft.use_state((0.0, 0.0))

    # Explicitly subscribe to observable properties used in build or contexts
    _ = app.locale
    _ = app.translations
    _ = app.route
    _ = viewport_size

    # subscribe to page events as soon as possible
    ft.context.page.on_route_change = app.route_change
    ft.context.page.on_view_pop = app.view_popped

    # stable callbacks
    toggle_mode = ft.use_callback(
        lambda: app.toggle_theme(), dependencies=[app.theme_mode]
    )
    set_theme_color = ft.use_callback(
        lambda color: app.set_theme_color(color), dependencies=[app.theme_color]
    )

    theme_value = ft.use_memo(
        lambda: ThemeContextValue(
            mode=app.theme_mode,
            seed_color=app.theme_color,
            toggle_mode=toggle_mode,
            set_seed_color=set_theme_color,
        ),
        dependencies=[app.theme_mode, app.theme_color, toggle_mode, set_theme_color],
    )

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
        lambda loc: app.set_locale(loc), dependencies=[app.locale]
    )

    locale_value = ft.use_memo(
        lambda: LocaleContextValue(
            locale=app.locale,
            translations=app.translations,
            set_locale=set_locale,
        ),
        dependencies=[app.locale, app.translations, set_locale],
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
    ) -> None:
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

            if stable_count >= stable_samples or loop.time() >= deadline:
                return

            await asyncio.sleep(poll_s)

    async def warmup_first_frame_update_task() -> None:
        # Delay the visible "first reflow" until the window size settles,
        # then force it before the user's first interaction.
        await wait_for_viewport_stable()
        ft.context.page.update()
        await wait_for_viewport_stable(timeout_s=0.8, stable_samples=2)
        sync_viewport_size()

    def on_page_resized(_: object) -> None:
        sync_viewport_size()

    def on_mounted() -> None:
        ft.context.page.title = "Tango Motors Control"
        ft.context.page.window.maximized = True
        ft.context.page.window.full_screen = True
        ft.context.page.window.frameless = True
        ft.context.page.on_resized = on_page_resized  # type: ignore[attr-defined]
        sync_viewport_size(force=True)
        # Global interaction tracking
        ft.context.page.on_pointer_down = lambda _: app.reset_timer()  # type: ignore[attr-defined]
        ft.context.page.on_keyboard_event = lambda _: app.reset_timer()
        ft.context.page.run_task(initialize_motors_task)
        ft.context.page.run_task(monitor_loop)
        ft.context.page.run_task(warmup_first_frame_update_task)

    ft.on_mounted(on_mounted)
    ft.on_unmounted(shutdown_motors_task)

    def update_theme() -> None:
        ft.context.page.theme_mode = app.theme_mode
        ft.context.page.theme = ft.context.page.dark_theme = ft.Theme(
            color_scheme_seed=app.theme_color
        )

    ft.on_updated(update_theme, [app.theme_mode, app.theme_color])

    return LocaleContext(
        locale_value,
        lambda: RouteContext(
            route_value,
            lambda: ThemeContext(
                theme_value,
                lambda: ft.View(
                    route="/",
                    padding=0,
                    controls=[Layout(app, AppBody(app))],
                ),
            ),
        ),
    )
