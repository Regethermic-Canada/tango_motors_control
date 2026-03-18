from collections.abc import Callable

import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from components.ui.button import TangoButton
from components.ui.card import TangoCard
from components.ui.icon_button import TangoIconButton
from components.ui.tag import TangoTag, TagVariant
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
    can_increment = motor.can_increment()
    can_decrement = motor.can_decrement()

    content_spacing = int(round(spacing.SM * metrics.scale))
    panel_spacing = int(round(spacing.LG * metrics.scale))
    speed_label_size = int(round((15 if metrics.is_compact else 16) * metrics.scale))
    speed_value_size = int(round((72 if metrics.is_compact else 76) * metrics.scale))
    speed_percent_size = int(round((18 if metrics.is_compact else 20) * metrics.scale))
    button_text_size = int(round((16 if metrics.is_compact else 17) * metrics.scale))
    panel_width = resolve_panel_width(
        metrics,
        compact_fraction=0.84,
        regular_fraction=0.60,
        compact_min=460,
        regular_min=560,
        max_width=820,
        edge_padding=spacing.XL,
    )
    step_button_size = int(round((40 if metrics.is_compact else 48) * metrics.scale))
    step_icon_size = int(round((20 if metrics.is_compact else 22) * metrics.scale))
    step_spacing = int(
        round((spacing.SM if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    speed_value_width = int(round((112 if metrics.is_compact else 144) * metrics.scale))
    speed_control_width = (
        (step_button_size * 2) + speed_value_width + (step_spacing * 2)
    )
    card_padding = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    speed_value_gap = max(4, int(round(6 * metrics.scale)))

    status_variant: TagVariant = "success" if is_running else "secondary"
    status_label = (
        loc.t("motor_status_running") if is_running else loc.t("motor_status_stopped")
    )

    def build_toast_message(message_key: str) -> Callable[[], str]:
        return lambda: settings_service.t(message_key)

    def show_limit_toast(message_key: str) -> None:
        show_toast(
            page=ft.context.page,
            type=ToastType.WARNING,
            build=build_toast_message(message_key),
        )

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

    def on_increment_click(_: Event[ft.IconButton]) -> None:
        changed = motor.increment()
        if changed and not motor.can_increment():
            show_limit_toast("max_speed_reached")

    def on_decrement_click(_: Event[ft.IconButton]) -> None:
        changed = motor.decrement()
        if changed and not motor.can_decrement():
            show_limit_toast("min_speed_reached")

    return TangoCard(
        width=panel_width,
        padding=ft.Padding(card_padding, card_padding, card_padding, card_padding),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            spacing=panel_spacing,
            controls=[
                TangoTag(status_label, variant=status_variant),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=content_spacing,
                    controls=[
                        TangoText(
                            loc.t("speed"),
                            variant="overline",
                            size=speed_label_size,
                            color=colors.TEXT_SOFT,
                        ),
                        ft.Container(
                            width=speed_control_width,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=speed_value_gap,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=step_spacing,
                                        controls=[
                                            TangoIconButton(
                                                icon=ft.Icons.REMOVE,
                                                icon_size=step_icon_size,
                                                on_click=on_decrement_click,
                                                tooltip=loc.t("decrement"),
                                                variant="surface",
                                                size=(
                                                    "lg"
                                                    if not metrics.is_compact
                                                    else "md"
                                                ),
                                                disabled=not can_decrement,
                                            ),
                                            ft.Container(
                                                width=speed_value_width,
                                                alignment=ft.Alignment.CENTER,
                                                content=TangoText(
                                                    str(motor.speed_level),
                                                    variant="display",
                                                    size=speed_value_size,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                            ),
                                            TangoIconButton(
                                                icon=ft.Icons.ADD,
                                                icon_size=step_icon_size,
                                                on_click=on_increment_click,
                                                tooltip=loc.t("increment"),
                                                variant="primary",
                                                size=(
                                                    "lg"
                                                    if not metrics.is_compact
                                                    else "md"
                                                ),
                                                disabled=not can_increment,
                                            ),
                                        ],
                                    ),
                                    TangoText(
                                        f"{motor.speed_percent}%",
                                        variant="subtitle",
                                        size=speed_percent_size,
                                        color=colors.TEXT_MUTED,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    width=panel_width - (card_padding * 2),
                    content=TangoButton(
                        text=(
                            loc.t("stop_motors")
                            if is_running
                            else loc.t("start_motors")
                        ),
                        expand=True,
                        icon=ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW,
                        tooltip=(
                            loc.t("stop_motors")
                            if is_running
                            else loc.t("start_motors")
                        ),
                        on_click=on_toggle_click,
                        size="lg" if not metrics.is_compact else "md",
                        text_size=button_text_size,
                        variant="surface" if is_running else "primary",
                    ),
                ),
            ],
        ),
    )
