from collections.abc import Callable

import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from components.ui.button import TangoButton
from components.ui.card import TangoCard
from components.ui.slider import TangoSlider
from components.ui.text import TangoText
from components.ui.tango_toast import ToastType, show_toast
from contexts.locale import LocaleContext
from contexts.motor import MotorContext
from contexts.settings import SettingsContext
from models.motor_types import MotorAction
from services.motors.tray_speed import sec_per_tray_to_trays_per_minute
from theme import colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics, resolve_panel_width


@ft.component
def MotorsView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    motor = ft.use_context(MotorContext).current()
    settings_service = ft.use_context(SettingsContext).current()
    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        base_width=960,
        base_height=540,
        min_scale=0.8,
    )
    is_running = motor.is_motors_running
    tray_setting_draft, set_tray_setting_draft = ft.use_state(float(motor.sec_per_tray))

    def sync_tray_setting_draft() -> None:
        set_tray_setting_draft(float(motor.sec_per_tray))

    ft.use_effect(sync_tray_setting_draft, [motor.sec_per_tray])

    tray_rate_preview = sec_per_tray_to_trays_per_minute(tray_setting_draft)
    control_min = motor.sec_per_tray_min
    control_max = motor.sec_per_tray_max
    control_divisions = max(
        1, int(round(motor.sec_per_tray_max - motor.sec_per_tray_min))
    )

    content_spacing = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    panel_spacing = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    speed_value_size = int(round((54 if metrics.is_compact else 64) * metrics.scale))
    speed_unit_size = int(round((22 if metrics.is_compact else 24) * metrics.scale))
    speed_number_width = int(
        round((150 if metrics.is_compact else 180) * metrics.scale)
    )
    panel_width = resolve_panel_width(
        metrics,
        compact_fraction=0.84,
        regular_fraction=0.60,
        compact_min=460,
        regular_min=560,
        max_width=820,
        edge_padding=spacing.XL,
    )
    slider_scale = max(1.06, metrics.scale * 1.04)
    card_padding = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    action_gap = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    value_row_gap = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    value_action_gap = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    value_block_padding_y = int(
        round((spacing.XS if metrics.is_compact else spacing.SM) * metrics.scale)
    )
    toggle_icon_size = int(round((52 if metrics.is_compact else 60) * metrics.scale))

    def build_toast_message(message_key: str) -> Callable[[], str]:
        return lambda: settings_service.t(message_key)

    def build_raw_toast_message(message: str) -> Callable[[], str]:
        return lambda: message

    def on_toggle_click(_: Event[Button]) -> None:
        result = motor.toggle_motors()

        message_key = "motors_action_failed"
        toast_type = ToastType.ERROR
        toast_build = build_toast_message(message_key)
        if result.action == MotorAction.STARTED:
            message_key = "motors_start_success"
            toast_type = ToastType.SUCCESS
            toast_build = build_toast_message(message_key)
        elif result.action == MotorAction.STOPPED:
            message_key = "motors_stop_success"
            toast_type = ToastType.INFO
            toast_build = build_toast_message(message_key)
        elif result.action == MotorAction.START_BLOCKED_BY_SAFETY:
            toast_type = ToastType.WARNING
            toast_build = (
                build_raw_toast_message(result.error)
                if result.error
                else build_toast_message("motors_start_blocked_by_safety")
            )
        elif result.action == MotorAction.START_FAILED_NO_MOTORS:
            message_key = "motors_start_no_motors"
            toast_build = build_toast_message(message_key)
        elif result.action == MotorAction.START_FAILED:
            message_key = "motors_start_failed"
            toast_build = build_toast_message(message_key)
        elif result.action == MotorAction.STOP_FAILED:
            message_key = "motors_stop_failed"
            toast_build = build_toast_message(message_key)

        show_toast(
            page=ft.context.page,
            type=toast_type,
            build=toast_build,
        )

    def on_control_value_change(value: float) -> None:
        bounded_value = max(
            motor.sec_per_tray_min, min(float(value), motor.sec_per_tray_max)
        )
        set_tray_setting_draft(bounded_value)

    def on_control_value_commit(value: float) -> None:
        committed_sec_per_tray = max(
            motor.sec_per_tray_min,
            min(float(value), motor.sec_per_tray_max),
        )
        set_tray_setting_draft(committed_sec_per_tray)
        changed = motor.set_sec_per_tray(committed_sec_per_tray)
        if not changed:
            return

        if committed_sec_per_tray <= motor.sec_per_tray_min:
            show_toast(
                page=ft.context.page,
                type=ToastType.WARNING,
                build=build_toast_message("min_tray_time_reached"),
            )
            return

        if committed_sec_per_tray >= motor.sec_per_tray_max:
            show_toast(
                page=ft.context.page,
                type=ToastType.WARNING,
                build=build_toast_message("max_tray_time_reached"),
            )
            return

        show_toast(
            page=ft.context.page,
            type=ToastType.INFO,
            build=build_toast_message("tray_time_updated"),
        )

    return TangoCard(
        width=panel_width,
        padding=ft.Padding(card_padding, card_padding, card_padding, card_padding),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            spacing=panel_spacing,
            controls=[
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=content_spacing,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=value_action_gap,
                            controls=[
                                ft.Container(
                                    padding=ft.Padding(
                                        0,
                                        value_block_padding_y,
                                        0,
                                        value_block_padding_y,
                                    ),
                                    content=ft.Row(
                                        vertical_alignment=ft.CrossAxisAlignment.END,
                                        spacing=value_row_gap,
                                        controls=[
                                            ft.Container(
                                                width=speed_number_width,
                                                alignment=ft.Alignment.CENTER_RIGHT,
                                                content=TangoText(
                                                    str(int(round(tray_setting_draft))),
                                                    variant="display",
                                                    size=speed_value_size,
                                                    text_align=ft.TextAlign.RIGHT,
                                                ),
                                            ),
                                            TangoText(
                                                loc.t("seconds_per_tray_unit"),
                                                variant="subtitle",
                                                size=speed_unit_size,
                                                color=colors.TEXT_MUTED,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                TangoText(
                                    f"{tray_rate_preview:.1f} {loc.t('trays_per_minute_unit')}",
                                    variant="caption",
                                    size=speed_unit_size,
                                    color=colors.TEXT_MUTED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                        TangoSlider(
                            min=control_min,
                            max=control_max,
                            divisions=control_divisions,
                            label="{value}",
                            value=tray_setting_draft,
                            set_value=on_control_value_change,
                            on_commit=on_control_value_commit,
                            scale=slider_scale,
                        ),
                    ],
                ),
                (
                    ft.Column(
                        spacing=action_gap,
                        controls=[
                            TangoButton(
                                expand=True,
                                icon=(
                                    ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW
                                ),
                                icon_only=True,
                                icon_size=toggle_icon_size,
                                tooltip=(
                                    loc.t("stop_motors")
                                    if is_running
                                    else loc.t("start_motors")
                                ),
                                on_click=on_toggle_click,
                                size="xl",
                                variant="error" if is_running else "primary",
                            ),
                        ],
                    )
                    if metrics.is_compact
                    else ft.Row(
                        spacing=0,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=TangoButton(
                                    expand=True,
                                    icon=(
                                        ft.Icons.STOP
                                        if is_running
                                        else ft.Icons.PLAY_ARROW
                                    ),
                                    icon_only=True,
                                    icon_size=toggle_icon_size,
                                    tooltip=(
                                        loc.t("stop_motors")
                                        if is_running
                                        else loc.t("start_motors")
                                    ),
                                    on_click=on_toggle_click,
                                    size="xl",
                                    variant="error" if is_running else "primary",
                                ),
                            ),
                        ],
                    )
                ),
            ],
        ),
    )
