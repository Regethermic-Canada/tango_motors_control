from typing import Any
import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)

    def on_timeout_change(e: Any) -> None:
        if e.control and hasattr(e.control, "value"):
            app_model.set_inactivity_timeout(float(e.control.value))

    return ft.Container(
        expand=True,
        padding=ft.Padding(40, 40, 40, 40),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=30,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            loc.t("admin_settings"),
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                ft.Divider(),
                # Inactivity Timeout Section
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    loc.t("inactivity_timeout"),
                                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                ),
                                ft.Text(
                                    f"{int(app_model.inactivity_limit)} {loc.t('seconds')}"
                                ),
                            ],
                        ),
                        ft.Slider(
                            min=10,
                            max=150,
                            divisions=14,
                            label="{value}s",
                            value=app_model.inactivity_limit,
                            on_change=on_timeout_change,
                        ),
                    ],
                ),
            ],
        ),
    )
