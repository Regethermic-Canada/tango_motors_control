import flet as ft
from typing import Callable, Any


@ft.component
def Screensaver(asset_path: str, on_click: Callable[[Any], None]) -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK,
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        content=ft.Image(src=asset_path, fit=ft.BoxFit.COVER, opacity=0.8),
    )
