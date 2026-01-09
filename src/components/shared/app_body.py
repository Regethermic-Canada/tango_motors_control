import flet as ft
from components.admin.admin_view import AdminView
from components.main.main_view import MainView
from contexts.route import RouteContext
from models.app_model import AppModel


@ft.component
def AppBody(app_model: AppModel) -> ft.Control:
    route_ctx = ft.use_context(RouteContext)

    if route_ctx.route == "/admin":
        return AdminView(app_model)
    return MainView(app_model)
