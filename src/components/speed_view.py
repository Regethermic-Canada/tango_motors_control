import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext


@ft.component
def SpeedView(model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        tight=True,
        controls=[
            ft.Text(
                loc.t("speed"),
                size=20,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                value=str(model.speed_level),
                size=80,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=40,
                        on_click=lambda _: model.decrement(),
                        tooltip=loc.t("decrement"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=40,
                        on_click=lambda _: model.increment(),
                        tooltip=loc.t("increment"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=40,
            ),
        ],
    )
