import flet as ft
from models.app_model import AppModel


@ft.component
def CounterView(model: AppModel) -> ft.Control:
    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        tight=True,
        controls=[
            ft.Text(
                value=str(model.counter_val),
                size=80,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=40,
                        on_click=lambda _: model.decrement(),
                        key="increment_speed_btn",
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=40,
                        on_click=lambda _: model.increment(),
                        key="decrement_speed_btn",
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=40,
            ),
        ],
    )
