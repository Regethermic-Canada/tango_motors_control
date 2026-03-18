import logging
import asyncio
import flet as ft

from components.ui.card import TangoCard
from components.ui.page import TangoPage
from components.ui.text import TangoText
from components.ui.toast import ToastType, show_toast
from contexts.locale import LocaleContext
from contexts.route import RouteContext
from contexts.settings import SettingsContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics
from components.ui.numpad import TangoNumpad

logger = logging.getLogger(__name__)


@ft.component
def AuthView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    route_ctx = ft.use_context(RouteContext)
    settings_service = ft.use_context(SettingsContext).current()
    passcode, set_passcode = ft.use_state("")
    shake_offset, set_shake_offset = ft.use_state(ft.Offset(0, 0))

    async def on_route_changed() -> None:
        await asyncio.sleep(0.2)
        set_passcode("")

    ft.on_updated(on_route_changed, [route_ctx.route])

    async def verify_passcode(current_passcode: str) -> None:
        # Small delay to let the 4th dot render
        await asyncio.sleep(0.1)
        authenticated = await asyncio.to_thread(
            settings_service.verify_admin_passcode,
            current_passcode,
        )

        if authenticated:
            set_passcode("")
            show_toast(
                page=ft.context.page,
                message=loc.t("admin_access_granted"),
                type=ToastType.SUCCESS,
            )
            route_ctx.navigate("/admin")
        else:
            # Show toast simultaneously with shake
            show_toast(
                page=ft.context.page,
                message=loc.t("invalid_passcode"),
                type=ToastType.ERROR,
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

    content_spacing = int(
        round((spacing.MD if metrics.compact else spacing.LG) * metrics.scale)
    )
    dots_font_size = int(round((22 if metrics.compact else 28) * metrics.scale))
    dots_letter_spacing = int(round((5 if metrics.compact else 7) * metrics.scale))
    card_width = min(
        680,
        max(360 if metrics.compact else 520, int(metrics.width * 0.54)),
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
            controls=[
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
                            TangoNumpad(
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
