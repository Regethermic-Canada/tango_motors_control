import flet as ft


@ft.component
def Screensaver(asset_path: str) -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK,
        alignment=ft.Alignment.CENTER,
        content=ft.Image(src=asset_path, fit=ft.BoxFit.COVER),
    )
