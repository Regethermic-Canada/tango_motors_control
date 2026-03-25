import logging
import asyncio
import flet as ft

from components.ui.card import TangoCard
from components.ui.numpad import TangoNumpad
from components.ui.page import TangoPage
from components.ui.passcode_indicator import (
    PASSCODE_LENGTH,
    PasscodeIndicator,
    animate_passcode_shake,
)
from components.ui.tango_toast import ToastType, show_toast
from contexts.route import RouteContext
from contexts.settings import SettingsContext
from theme import spacing
from theme.scale import ViewportArea, get_viewport_metrics, resolve_panel_width

logger = logging.getLogger(__name__)


@ft.component
def AuthView() -> ft.Control:
    page = ft.context.page
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

            def apply_shake_offset(point: ft.Offset) -> None:
                set_shake_offset(point)
                page.update()

            await animate_passcode_shake(
                apply_offset=apply_shake_offset,
            )
            set_passcode("")

    def on_digit_click(digit: str) -> None:
        if len(passcode) < PASSCODE_LENGTH:
            new_passcode = passcode + digit
            set_passcode(new_passcode)
            if len(new_passcode) == PASSCODE_LENGTH:
                asyncio.create_task(verify_passcode(new_passcode))

    def on_clear_click() -> None:
        set_passcode("")

    def on_backspace_click() -> None:
        if len(passcode) > 0:
            set_passcode(passcode[:-1])

    metrics = get_viewport_metrics(page, area=ViewportArea.CONTENT, min_scale=0.7)
    content_spacing = int(
        round((spacing.MD if metrics.is_compact else spacing.LG) * metrics.scale)
    )
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
                            PasscodeIndicator(
                                passcode=passcode,
                                scale=metrics.scale,
                                is_compact=metrics.is_compact,
                                offset=shake_offset,
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
