import flet as ft
from components.native.page import TangoPage
from .motors_view import MotorsView


@ft.component
def MainView() -> ft.Control:
    return TangoPage(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=MotorsView(),
    )
