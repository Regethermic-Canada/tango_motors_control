from collections.abc import Callable

import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from components.ui.button import TangoButton
from components.ui.card import TangoCard
from components.ui.icon_button import TangoIconButton, IconButtonVariant
from components.ui.slider import TangoSlider
from components.ui.text import TangoText
from components.ui.tango_toast import ToastType, show_toast
from contexts.locale import LocaleContext
from contexts.motor import MotorContext
from contexts.settings import SettingsContext
from models.motor_types import MotorAction
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
    plate_time_draft, set_plate_time_draft = ft.use_state(float(motor.sec_per_plate))

    def sync_plate_time_draft() -> None:
        set_plate_time_draft(float(motor.sec_per_plate))

    ft.use_effect(sync_plate_time_draft, [motor.sec_per_plate])

    preview_sec_per_plate = float(round(plate_time_draft))

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
    reverse_icon_size = int(round((22 if metrics.is_compact else 24) * metrics.scale))
    value_row_gap = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    value_action_gap = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    value_block_padding_y = int(
        round((spacing.XS if metrics.is_compact else spacing.SM) * metrics.scale)
    )
    direction_button_offset = int(
        round((spacing.MD if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    toggle_icon_size = int(round((52 if metrics.is_compact else 60) * metrics.scale))

    direction_icon = (
        ft.Icons.ARROW_BACK if motor.is_reversed else ft.Icons.ARROW_FORWARD
    )
    direction_button_variant: IconButtonVariant = (
        "warning" if motor.is_reversed else "primary"
    )

    def build_toast_message(message_key: str) -> Callable[[], str]:
        return lambda: settings_service.t(message_key)

    def on_toggle_click(_: Event[Button]) -> None:
        result = motor.toggle_motors()

        message_key = "motors_action_failed"
        toast_type = ToastType.ERROR
        if result.action == MotorAction.STARTED:
            message_key = "motors_start_success"
            toast_type = ToastType.SUCCESS
        elif result.action == MotorAction.STOPPED:
            message_key = "motors_stop_success"
            toast_type = ToastType.INFO
        elif result.action == MotorAction.START_FAILED_NO_MOTORS:
            message_key = "motors_start_no_motors"
        elif result.action == MotorAction.START_FAILED:
            message_key = "motors_start_failed"
        elif result.action == MotorAction.STOP_FAILED:
            message_key = "motors_stop_failed"

        show_toast(
            page=ft.context.page,
            type=toast_type,
            build=build_toast_message(message_key),
        )

    def on_plate_time_commit(value: float) -> None:
        committed_value = float(round(value))
        set_plate_time_draft(committed_value)
        changed = motor.set_sec_per_plate(committed_value)
        if not changed:
            return

        if committed_value <= motor.sec_per_plate_min:
            show_toast(
                page=ft.context.page,
                type=ToastType.WARNING,
                build=build_toast_message("min_plate_time_reached"),
            )
            return

        if committed_value >= motor.sec_per_plate_max:
            show_toast(
                page=ft.context.page,
                type=ToastType.WARNING,
                build=build_toast_message("max_plate_time_reached"),
            )
            return

        show_toast(
            page=ft.context.page,
            type=ToastType.INFO,
            build=build_toast_message("plate_time_updated"),
        )

    def on_direction_click(_: Event[ft.IconButton]) -> None:
        motor.toggle_direction()
        show_toast(
            page=ft.context.page,
            type=ToastType.WARNING if motor.is_reversed else ToastType.INFO,
            build=build_toast_message(
                "direction_set_reverse"
                if motor.is_reversed
                else "direction_set_forward"
            ),
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
                                                    str(
                                                        int(
                                                            round(preview_sec_per_plate)
                                                        )
                                                    ),
                                                    variant="display",
                                                    size=speed_value_size,
                                                    text_align=ft.TextAlign.RIGHT,
                                                ),
                                            ),
                                            TangoText(
                                                loc.t("seconds_per_plate_unit"),
                                                variant="subtitle",
                                                size=speed_unit_size,
                                                color=colors.TEXT_MUTED,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                    ),
                                ),
                                ft.Container(
                                    margin=ft.Margin(direction_button_offset, 0, 0, 0),
                                    content=TangoIconButton(
                                        icon=direction_icon,
                                        on_click=on_direction_click,
                                        tooltip=(
                                            loc.t("set_forward")
                                            if motor.is_reversed
                                            else loc.t("set_reverse")
                                        ),
                                        variant=direction_button_variant,
                                        size="xl",
                                        icon_size=reverse_icon_size,
                                    ),
                                ),
                            ],
                        ),
                        TangoSlider(
                            min=motor.sec_per_plate_min,
                            max=motor.sec_per_plate_max,
                            divisions=int(
                                motor.sec_per_plate_max - motor.sec_per_plate_min
                            ),
                            label="{value}s",
                            value=plate_time_draft,
                            set_value=set_plate_time_draft,
                            on_commit=on_plate_time_commit,
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
                                variant="surface" if is_running else "primary",
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
                                    variant="surface" if is_running else "primary",
                                ),
                            ),
                        ],
                    )
                ),
            ],
        ),
    )
