from typing import Any
import flet as ft
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from models.app_model import AppModel
from contexts.locale import LocaleContext
from utils.config import config


class DigitButton(ft.TextButton):
    def __init__(self, text: str, on_click: Any) -> None:
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.content = ft.Text(text, size=24, weight=ft.FontWeight.W_500)
        self.style = ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.Padding(25, 25, 25, 25),
        )


@ft.component
def AuthView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    passcode, set_passcode = ft.use_state("")
    error_message, set_error_message = ft.use_state("")
    ph = PasswordHasher()

    def on_digit_click(e: ft.ControlEvent) -> None:
        if len(passcode) < 6:  # Reasonable limit for passcode
            digit = getattr(e.control, "text", "")
            set_passcode(passcode + digit)
            set_error_message("")

    def on_clear_click(e: ft.ControlEvent) -> None:
        set_passcode("")
        set_error_message("")

    def on_backspace_click(e: ft.ControlEvent) -> None:
        if len(passcode) > 0:
            set_passcode(passcode[:-1])
            set_error_message("")

    def on_login_click(e: ft.ControlEvent) -> None:
        stored_hash = config.admin_passcode_hash
        default_passcode = config.app_admin_default_passcode

        authenticated = False
        try:
            if not stored_hash:
                # Fallback to default passcode if no hash is set
                if passcode == default_passcode:
                    authenticated = True
                    # Auto-hash and save for future use
                    new_hash = ph.hash(passcode)
                    config.set("ADMIN_PASSCODE_HASH", new_hash)
            else:
                ph.verify(stored_hash, passcode)
                authenticated = True
        except VerifyMismatchError:
            authenticated = False
        except Exception as ex:
            print(f"Auth error: {ex}")
            authenticated = False

        if authenticated:
            app_model.navigate("/admin")
        else:
            set_error_message(loc.t("invalid_passcode"))
            set_passcode("")

    return ft.Container(
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, size=50, color=ft.Colors.PRIMARY),
                        ft.Text(
                            loc.t("admin_access"),
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                ),
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "● " * len(passcode) if passcode else loc.t("enter_passcode"),
                                        size=30,
                                        style=ft.TextStyle(letter_spacing=5),
                                        color=ft.Colors.PRIMARY if passcode else ft.Colors.OUTLINE,
                                    )
                                ],
                            ),
                            ft.Text(
                                error_message,
                                color=ft.Colors.ERROR,
                                visible=bool(error_message),
                            ),
                            ft.Container(
                                width=280,
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                            controls=[
                                                DigitButton("1", on_digit_click),
                                                DigitButton("2", on_digit_click),
                                                DigitButton("3", on_digit_click),
                                            ]
                                        ),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                            controls=[
                                                DigitButton("4", on_digit_click),
                                                DigitButton("5", on_digit_click),
                                                DigitButton("6", on_digit_click),
                                            ]
                                        ),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                            controls=[
                                                DigitButton("7", on_digit_click),
                                                DigitButton("8", on_digit_click),
                                                DigitButton("9", on_digit_click),
                                            ]
                                        ),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                                            controls=[
                                                ft.IconButton(
                                                    icon=ft.Icons.BACKSPACE_OUTLINED,
                                                    on_click=on_backspace_click,
                                                    icon_size=24,
                                                ),
                                                DigitButton("0", on_digit_click),
                                                ft.IconButton(
                                                    icon=ft.Icons.CLEAR_ALL,
                                                    on_click=on_clear_click,
                                                    icon_size=24,
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                            ),
                            ft.ElevatedButton(
                                loc.t("login"),
                                icon=ft.Icons.LOGIN,
                                on_click=on_login_click,
                                width=280,
                                height=60,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                            ft.TextButton(
                                loc.t("back"),
                                on_click=lambda _: app_model.navigate("/"),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
