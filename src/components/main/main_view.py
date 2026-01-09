import flet as ft
from .motors_view import MotorsView
from models.app_model import AppModel


@ft.component
def MainView(app_model: AppModel) -> ft.Control:
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=MotorsView(app_model),
    )
