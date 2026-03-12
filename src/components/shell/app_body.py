import flet as ft
from contexts.route import RouteContext
from models.app_model import AppModel
from views.admin.admin_view import AdminView
from views.admin.auth_view import AuthView
from views.main.main_view import MainView


@ft.component
def AppBody(app_model: AppModel) -> ft.Control:
    route_ctx = ft.use_context(RouteContext)

    if route_ctx.route == "/admin":
        return AdminView(app_model)
    elif route_ctx.route == "/auth":
        return AuthView(app_model)
    return MainView(app_model)
