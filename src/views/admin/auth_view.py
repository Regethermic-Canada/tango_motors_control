import logging
import asyncio
import flet as ft

from components.ui.card import TangoCard
from components.ui.numpad import TangoNumpad
from components.ui.page import TangoPage
from components.ui.text import TangoText
from components.ui.tango_toast import ToastType, show_toast
from contexts.route import RouteContext
from contexts.settings import SettingsContext
from theme import animation, colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics, resolve_panel_width

logger = logging.getLogger(__name__)


@ft.component
def AuthView() -> ft.Control:
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
                type=ToastType.SUCCESS,
                build=lambda: settings_service.t("admin_access_granted"),
            )
            route_ctx.navigate("/admin")
        else:
            # Show toast simultaneously with shake
            show_toast(
                page=ft.context.page,
                type=ToastType.ERROR,
                build=lambda: settings_service.t("invalid_passcode"),
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

    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        min_scale=0.7,
    )

    dots = "".join(
        "● " if index < len(passcode) else "○ " for index in range(4)
    ).strip()
    content_spacing = int(
        round((spacing.MD if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    dots_font_size = int(round((28 if metrics.is_compact else 34) * metrics.scale))
    dots_letter_spacing = int(round((8 if metrics.is_compact else 10) * metrics.scale))
    card_width = resolve_panel_width(
        metrics,
        compact_fraction=0.64,
        regular_fraction=0.52,
        compact_min=420,
        regular_min=520,
        max_width=700,
        edge_padding=spacing.XL,
    )
    card_padding = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
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
                                animate_offset=animation.make(
                                    animation.AUTH_SHAKE_MS,
                                    animation.AUTH_SHAKE_CURVE,
                                ),
                                content=TangoText(
                                    dots,
                                    variant="headline",
                                    size=dots_font_size,
                                    letter_spacing=dots_letter_spacing,
                                    color=(
                                        colors.PRIMARY if passcode else colors.OUTLINE
                                    ),
                                    text_align=ft.TextAlign.CENTER,
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
