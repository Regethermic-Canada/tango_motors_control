import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.container import Container

ClickHandler = ControlEventHandler[Container]


@ft.component
def Screensaver(asset_path: str, on_click: ClickHandler) -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK,
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        content=ft.Image(src=asset_path, fit=ft.BoxFit.COVER),
    )
