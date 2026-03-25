import asyncio
from collections.abc import Callable

import flet as ft

from components.ui.numpad import TangoNumpad
from components.ui.passcode_indicator import (
    PASSCODE_LENGTH,
    PasscodeIndicator,
    animate_passcode_shake,
)
from components.ui.tango_toast import ToastType, show_toast
from contexts.locale import LocaleContext
from contexts.settings import SettingsContext
from theme import colors, spacing, typography
from theme.scale import ViewportArea, get_viewport_metrics


@ft.component
def AdminPasscodeSheet(*, on_close: Callable[[], None]) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    settings_service = ft.use_context(SettingsContext).current()
    page = ft.context.page
    new_passcode, set_new_passcode = ft.use_state("")
    confirm_passcode, set_confirm_passcode = ft.use_state("")
    is_saving, set_is_saving = ft.use_state(False)
    shake_offset, set_shake_offset = ft.use_state(ft.Offset(0, 0))
    metrics = get_viewport_metrics(
        page,
        area=ViewportArea.CONTENT,
        min_scale=0.64,
    )
    sheet_spacing = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    helper_spacing = int(round(spacing.XS * metrics.scale))
    top_padding = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    bottom_padding = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    instruction_size = int(round((18 if metrics.is_compact else 20) * metrics.scale))
    helper_size = int(round((14 if metrics.is_compact else 15) * metrics.scale))
    content_width = min(
        560, int(metrics.width * (0.88 if metrics.is_compact else 0.72))
    )
    is_confirming = len(new_passcode) == PASSCODE_LENGTH
    active_passcode = confirm_passcode if is_confirming else new_passcode
    instruction = loc.t(
        "confirm_admin_passcode" if is_confirming else "new_admin_passcode"
    )
    helper = loc.t("saving" if is_saving else "admin_passcode_hint")
    step_value = "2 / 2" if is_confirming else "1 / 2"

    async def save_passcode(passcode: str) -> None:
        await asyncio.sleep(0.1)
        try:
            await asyncio.to_thread(settings_service.update_admin_passcode, passcode)
        except Exception:
            show_toast(
                page=page,
                type=ToastType.ERROR,
                build=lambda: loc.t("admin_passcode_update_failed"),
            )
            set_is_saving(False)
            return

        show_toast(
            page=page,
            type=ToastType.SUCCESS,
            build=lambda: loc.t("admin_passcode_updated"),
        )
        set_is_saving(False)
        on_close()

    async def handle_mismatch() -> None:
        await asyncio.sleep(0.1)
        show_toast(
            page=page,
            type=ToastType.ERROR,
            build=lambda: loc.t("admin_passcode_mismatch"),
        )

        def apply_shake_offset(point: ft.Offset) -> None:
            set_shake_offset(point)
            page.update()

        await animate_passcode_shake(apply_offset=apply_shake_offset)
        set_confirm_passcode("")
        set_new_passcode("")

    def on_digit_click(digit: str) -> None:
        if is_saving:
            return

        if not is_confirming:
            if len(new_passcode) < PASSCODE_LENGTH:
                set_new_passcode(new_passcode + digit)
            return

        if len(confirm_passcode) >= PASSCODE_LENGTH:
            return

        next_confirm_passcode = confirm_passcode + digit
        set_confirm_passcode(next_confirm_passcode)
        if len(next_confirm_passcode) < PASSCODE_LENGTH:
            return
        if next_confirm_passcode != new_passcode:
            asyncio.create_task(handle_mismatch())
            return

        set_is_saving(True)
        asyncio.create_task(save_passcode(next_confirm_passcode))

    def on_clear_click() -> None:
        if is_saving:
            return
        if is_confirming:
            set_confirm_passcode("")
            return
        set_new_passcode("")

    def on_backspace_click() -> None:
        if is_saving:
            return
        if is_confirming:
            if confirm_passcode:
                set_confirm_passcode(confirm_passcode[:-1])
            return
        if new_passcode:
            set_new_passcode(new_passcode[:-1])

    return ft.Container(
        width=content_width,
        padding=ft.Padding(0, top_padding, 0, bottom_padding),
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=sheet_spacing,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=helper_spacing,
                    controls=[
                        ft.Text(
                            value=step_value,
                            style=typography.text_style(
                                "overline",
                                color=colors.TEXT_SOFT,
                                size=helper_size,
                            ),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            value=instruction,
                            style=typography.text_style(
                                "subtitle",
                                size=instruction_size,
                            ),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            value=helper,
                            style=typography.text_style(
                                "caption",
                                color=colors.TEXT_MUTED,
                                size=helper_size,
                            ),
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
                PasscodeIndicator(
                    passcode=active_passcode,
                    scale=metrics.scale,
                    is_compact=metrics.is_compact,
                    offset=shake_offset,
                ),
                TangoNumpad(
                    on_digit_click=on_digit_click,
                    on_backspace_click=on_backspace_click,
                    on_clear_click=on_clear_click,
                    scale_factor=0.88 if metrics.is_compact else 0.94,
                ),
            ],
        ),
    )
