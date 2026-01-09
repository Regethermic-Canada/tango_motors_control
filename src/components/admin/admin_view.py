from typing import Any
import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext
from components.shared.toast import show_toast, ToastType


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)

    def on_timeout_change(e: Any) -> None:
        if e.control and hasattr(e.control, "value"):
            app_model.set_inactivity_timeout(float(e.control.value))

    new_passcode_ref = ft.Ref[ft.BaseControl]()
    confirm_passcode_ref = ft.Ref[ft.BaseControl]()
    passcode_error, set_passcode_error = ft.use_state("")
    passcode_success, set_passcode_success = ft.use_state(False)

    def on_change_passcode(e: Any) -> None:
        if not new_passcode_ref.current or not confirm_passcode_ref.current:
            return

        tf1 = new_passcode_ref.current
        tf2 = confirm_passcode_ref.current

        assert isinstance(tf1, ft.TextField)
        assert isinstance(tf2, ft.TextField)

        p1 = tf1.value
        p2 = tf2.value
        if not p1 or not p2:
            return

        if len(p1) != 4:
            set_passcode_error(
                loc.t("passcode_mismatch")
            )  # Or a more specific error if needed
            return

        if p1 == p2:
            app_model.update_admin_passcode(p1)
            set_passcode_error("")
            set_passcode_success(True)
            tf1.value = ""
            tf2.value = ""
            tf1.update()
            tf2.update()
            show_toast(
                page=ft.context.page,
                message=loc.t("passcode_updated"),
                type=ToastType.SUCCESS,
                close_tooltip=loc.t("close"),
            )
        else:
            set_passcode_error(loc.t("passcode_mismatch"))
            set_passcode_success(False)

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
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: app_model.navigate("/"),
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
                ft.Divider(),
                # Change Passcode Section
                ft.Column(
                    spacing=15,
                    controls=[
                        ft.Text(
                            loc.t("change_passcode"),
                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        ),
                        ft.TextField(
                            ref=new_passcode_ref,
                            label=loc.t("new_passcode"),
                            password=True,
                            can_reveal_password=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=300,
                            max_length=4,
                        ),
                        ft.TextField(
                            ref=confirm_passcode_ref,
                            label=loc.t("confirm_passcode"),
                            password=True,
                            can_reveal_password=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=300,
                            max_length=4,
                        ),
                        ft.Text(
                            passcode_error,
                            color=ft.Colors.ERROR,
                            visible=bool(passcode_error),
                        ),
                        ft.ElevatedButton(
                            loc.t("save"),
                            icon=ft.Icons.SAVE,
                            on_click=on_change_passcode,
                        ),
                    ],
                ),
            ],
        ),
    )
