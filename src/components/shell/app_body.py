import flet as ft
from contexts.route import RouteContext
from theme import animation
from views.admin.admin_view import AdminView
from views.admin.auth_view import AuthView
from views.main.main_view import MainView


@ft.component
def AppBody() -> ft.Control:
    route_ctx = ft.use_context(RouteContext)
    active_route = route_ctx.route

    def route_layer(route: str, content: ft.Control) -> ft.Container:
        is_active = route == active_route
        return ft.Container(
            key=f"route-layer:{route}",
            expand=True,
            opacity=1 if is_active else 0,
            ignore_interactions=not is_active,
            animate_opacity=animation.make(
                animation.ROUTE_FADE_MS,
                animation.ROUTE_FADE_CURVE,
            ),
            content=content,
        )

    return ft.Stack(
        expand=True,
        fit=ft.StackFit.EXPAND,
        controls=[
            route_layer("/", MainView()),
            route_layer("/auth", AuthView()),
            route_layer("/admin", AdminView()),
        ],
    )
