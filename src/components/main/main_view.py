import flet as ft
from .speed_view import SpeedView
from models.app_model import AppModel

@ft.component
def MainView(app_model: AppModel) -> ft.Control:
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=SpeedView(app_model),
    )