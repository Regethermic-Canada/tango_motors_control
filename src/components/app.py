import flet as ft

from components.main_view import MainView
from contexts.route import RouteContext, RouteContextValue
from contexts.theme import ThemeContext, ThemeContextValue
from models.app_model import AppModel


@ft.component
def App() -> ft.Control:
    app, _ = ft.use_state(AppModel(route=ft.context.page.route))

    # subscribe to page events as soon as possible
    ft.context.page.on_route_change = app.route_change
    ft.context.page.on_view_pop = app.view_popped

    # stable callbacks (don’t change identity each render)
    toggle_mode = ft.use_callback(
        lambda: app.toggle_theme(), dependencies=[app.theme_mode]
    )
    set_theme_color = ft.use_callback(
        lambda color: app.set_theme_color(color), dependencies=[app.theme_color]
    )

    # memoize the provided value so its identity changes only when mode changes
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

    def on_mounted() -> None:
        ft.context.page.title = "Tango Motors Control"

    ft.on_mounted(on_mounted)

    def update_theme() -> None:
        ft.context.page.theme_mode = app.theme_mode
        ft.context.page.theme = ft.context.page.dark_theme = ft.Theme(
            color_scheme_seed=app.theme_color
        )

    ft.on_updated(update_theme, [app.theme_mode, app.theme_color])

    return RouteContext(
        route_value,
        lambda: ThemeContext(
            theme_value,
            lambda: ft.View(
                route="/",
                padding=0,
                controls=[MainView(app)],
            ),
        ),
    )
