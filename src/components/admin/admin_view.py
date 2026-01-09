import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)

    return ft.Container(
        expand=True,
        padding=ft.Padding(40, 80, 40, 40),  # Added top padding for global header
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text(
                    loc.t("admin_settings"),
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Divider(),
                ft.Text(
                    loc.t("application_config"),
                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                ),
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
                    subtitle=ft.Text(
                        f"{app_model.inactivity_limit} {loc.t('seconds')}"
                    ),
                    leading=ft.Icon(ft.Icons.TIMER),
                ),
            ],
        ),
    )
