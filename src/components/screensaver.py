import flet as ft
from typing import Callable, Any


class Screensaver(ft.Container):
    def __init__(self, asset_path: str, on_click: Callable[[Any], None]) -> None:
        super().__init__()
        self.expand = True
        self.bgcolor = ft.Colors.BLACK
        self.alignment = ft.Alignment.CENTER
        self.on_click = on_click
        self.content = ft.Image(src=asset_path, fit=ft.BoxFit.COVER, opacity=0.8)
