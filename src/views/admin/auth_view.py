import logging
import asyncio
import flet as ft
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from components.native.card import TangoCard
from components.native.page import TangoPage
from components.native.text import TangoText
from components.native.toast import ToastType, show_toast
from models.app_model import AppModel
from contexts.locale import LocaleContext
from utils.config import config
from theme import colors, spacing
from theme.scale import get_viewport_metrics
from components.views.admin.numpad import NumericNumpad

logger = logging.getLogger(__name__)


@ft.component
def AuthView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    passcode, set_passcode = ft.use_state("")
    shake_offset, set_shake_offset = ft.use_state(ft.Offset(0, 0))
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
                    ft.context.page.update()
                    await asyncio.sleep(0.03)

            set_shake_offset(ft.Offset(0, 0))
            ft.context.page.update()

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

    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    root_spacing = int(round(spacing.LG * metrics.scale))
    header_spacing = int(round(spacing.XS * metrics.scale))
    content_spacing = int(
        round((spacing.MD if metrics.compact else spacing.LG) * metrics.scale)
    )
    lock_icon_size = int(round((40 if metrics.compact else 44) * metrics.scale))
    title_font_size = int(round((26 if metrics.compact else 32) * metrics.scale))
    subtitle_font_size = int(round((14 if metrics.compact else 16) * metrics.scale))
    dots_font_size = int(round((30 if metrics.compact else 40) * metrics.scale))
    dots_letter_spacing = int(round((7 if metrics.compact else 10) * metrics.scale))
    card_width = min(
        560,
        max(340 if metrics.compact else 420, int(metrics.width * 0.46)),
    )
    card_padding = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )

    return TangoPage(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=root_spacing,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=header_spacing,
                    controls=[
                        ft.Icon(
                            ft.Icons.LOCK_OUTLINED,
                            size=lock_icon_size,
                            color=colors.PRIMARY,
                        ),
                        TangoText(
                            loc.t("admin_access"),
                            variant="title",
                            size=title_font_size,
                        ),
                        TangoText(
                            loc.t("enter_passcode"),
                            variant="body",
                            size=subtitle_font_size,
                            color=colors.TEXT_MUTED,
                        ),
                    ],
                ),
                TangoCard(
                    width=card_width,
                    padding=ft.Padding(
                        card_padding, card_padding, card_padding, card_padding
                    ),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=content_spacing,
                        controls=[
                            ft.Container(
                                offset=shake_offset,
                                animate_offset=ft.Animation(
                                    40, ft.AnimationCurve.LINEAR
                                ),
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        TangoText(
                                            dots.strip(),
                                            variant="headline",
                                            size=dots_font_size,
                                            letter_spacing=dots_letter_spacing,
                                            color=(
                                                colors.PRIMARY
                                                if passcode
                                                else colors.OUTLINE
                                            ),
                                        )
                                    ],
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
