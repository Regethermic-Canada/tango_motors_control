import flet as ft
from models.app_model import AppModel
from contexts.route import RouteContext
from contexts.locale import LocaleContext

@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    route_context = ft.use_context(RouteContext)
    loc = ft.use_context(LocaleContext)

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(loc.t("admin_settings"), theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: route_context.navigate("/")
                        ),
                    ]
                ),
                ft.Divider(),
                ft.Text(loc.t("application_config"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.ListTile(
                    title=ft.Text(loc.t("locale")),
                    subtitle=ft.Text(f"{app_model.locale}"),
                    leading=ft.Icon(ft.Icons.LANGUAGE),
                ),
                ft.ListTile(
                    title=ft.Text(loc.t("theme_mode")),
                    subtitle=ft.Text(f"{app_model.theme_mode.value}"),
                    leading=ft.Icon(ft.Icons.BRIGHTNESS_4),
                ),
                ft.ListTile(
                    title=ft.Text(loc.t("inactivity_timeout")),
                    subtitle=ft.Text(f"{app_model.inactivity_limit} {loc.t('seconds')}"),
                    leading=ft.Icon(ft.Icons.TIMER),
                ),
                ft.ElevatedButton(
                    loc.t("back_to_main"),
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: route_context.navigate("/")
                )
            ]
        )
    )