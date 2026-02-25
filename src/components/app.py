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

    def sync_viewport_size() -> None:
        next_size = (
            float(getattr(ft.context.page, "width", 0) or 0),
            float(getattr(ft.context.page, "height", 0) or 0),
        )
        prev_size = getattr(ft.context.page, "_last_synced_viewport_size", None)
        if (
            isinstance(prev_size, tuple)
            and len(prev_size) == 2
            and abs(float(prev_size[0]) - next_size[0]) <= 4
            and abs(float(prev_size[1]) - next_size[1]) <= 4
        ):
            return

        setattr(ft.context.page, "_last_synced_viewport_size", next_size)
        set_viewport_size(next_size)

    def on_mounted() -> None:
        ft.context.page.title = "Tango Motors Control"
        ft.context.page.window.maximized = True
        ft.context.page.window.full_screen = True
        ft.context.page.window.frameless = True
        ft.context.page.on_resized = lambda _e: sync_viewport_size()  # type: ignore[attr-defined]
        # Flush native window changes now to avoid a visible jump on the first toast update.
        ft.context.page.update()
        sync_viewport_size()
        # Global interaction tracking
        ft.context.page.on_pointer_down = lambda _: app.reset_timer()  # type: ignore[attr-defined]
        ft.context.page.on_keyboard_event = lambda _: app.reset_timer()
        ft.context.page.run_task(initialize_motors_task)
        ft.context.page.run_task(monitor_loop)

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
