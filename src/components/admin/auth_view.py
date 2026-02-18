import logging
import asyncio
import flet as ft
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from models.app_model import AppModel
from contexts.locale import LocaleContext
from utils.config import config
from components.shared.numpad import NumericNumpad
from components.shared.toast import show_toast, ToastType

logger = logging.getLogger(__name__)


@ft.component
def AuthView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    passcode, set_passcode = ft.use_state("")  # type: ignore
    shake_offset, set_shake_offset = ft.use_state(ft.Offset(0, 0))  # type: ignore
    ph = PasswordHasher()

    async def verify_passcode(current_passcode: str) -> None:
        stored_hash = config.admin_passcode_hash
        default_passcode = config.app_admin_default_passcode
        authenticated = False

        # Small delay to let the 4th dot render
        await asyncio.sleep(0.1)

        try:
            if not stored_hash:
                if current_passcode == default_passcode:
                    authenticated = True
                    new_hash = ph.hash(current_passcode)
                    config.set("ADMIN_PASSCODE_HASH", new_hash)
                    set_passcode("")
            else:
                ph.verify(stored_hash, current_passcode)
                authenticated = True
                set_passcode("")
        except VerifyMismatchError:
            authenticated = False
        except Exception as ex:
            logger.error(f"Auth error: {ex}")
            authenticated = False

        if authenticated:
            app_model.navigate("/admin")
        else:
            # Show toast simultaneously with shake
            show_toast(
                page=ft.context.page,
                message=loc.t("invalid_passcode"),
                type=ToastType.ERROR,
                close_tooltip=loc.t("close"),
            )

            # Multi-directional shake animation (More complex 4-point sequence)
            shake_points = [
                ft.Offset(0.02, 0.01),
                ft.Offset(-0.02, -0.01),
                ft.Offset(0.02, -0.01),
                ft.Offset(-0.02, 0.01),
            ]
            for _ in range(2):
                for point in shake_points:
                    set_shake_offset(point)
                    ft.context.page.update()  # type: ignore
                    await asyncio.sleep(0.03)

            set_shake_offset(ft.Offset(0, 0))
            ft.context.page.update()  # type: ignore

            set_passcode("")

    def on_digit_click(digit: str) -> None:
        if len(passcode) < 4:
            new_passcode = passcode + digit
            set_passcode(new_passcode)
            if len(new_passcode) == 4:
                asyncio.create_task(verify_passcode(new_passcode))

    def on_clear_click() -> None:
        set_passcode("")

    def on_backspace_click() -> None:
        if len(passcode) > 0:
            set_passcode(passcode[:-1])

    # Visual dots representation: ● for filled, ○ for empty
    dots = ""
    for i in range(4):
        dots += "● " if i < len(passcode) else "○ "

    return ft.Container(
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.LOCK_OUTLINED, size=50, color=ft.Colors.PRIMARY
                        ),
                        ft.Text(
                            loc.t("admin_access"),
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Container(
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            dots.strip(),
                                            size=40,
                                            style=ft.TextStyle(letter_spacing=10),
                                            color=(
                                                ft.Colors.PRIMARY
                                                if passcode
                                                else ft.Colors.OUTLINE
                                            ),
                                        )
                                    ],
                                ),
                                offset=shake_offset,
                                animate_offset=ft.Animation(
                                    40, ft.AnimationCurve.LINEAR
                                ),
                            ),
                            NumericNumpad(
                                on_digit_click=on_digit_click,
                                on_backspace_click=on_backspace_click,
                                on_clear_click=on_clear_click,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
