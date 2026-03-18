import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from components.ui.button import TangoButton
from components.ui.card import TangoCard
from components.ui.icon_button import TangoIconButton
from components.ui.tag import TangoTag, TagVariant
from components.ui.text import TangoText
from components.ui.toast import ToastType, show_toast
from models.motor_types import MotorAction
from contexts.locale import LocaleContext
from contexts.motor import MotorContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics


@ft.component
def MotorsView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    motor = ft.use_context(MotorContext).current()
    metrics = get_viewport_metrics(
        ft.context.page,
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
    panel_width = min(
        640,
        max(
            360 if metrics.is_compact else 500,
            int(metrics.width * (0.8 if metrics.is_compact else 0.52)),
        ),
    )
    step_button_size = int(round((40 if metrics.is_compact else 48) * metrics.scale))
    step_icon_size = int(round((20 if metrics.is_compact else 22) * metrics.scale))
    step_spacing = int(
        round((spacing.SM if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    speed_control_gap = int(
        round((spacing.XS if metrics.is_compact else spacing.SM) * metrics.scale)
    )
    speed_value_width = int(round((112 if metrics.is_compact else 144) * metrics.scale))
    speed_control_width = (
        (step_button_size * 2) + speed_value_width + (step_spacing * 2)
    )
    card_padding = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )

    status_variant: TagVariant = "success" if is_running else "secondary"
    status_label = (
        loc.t("motor_status_running") if is_running else loc.t("motor_status_stopped")
    )

    def show_limit_toast(message_key: str) -> None:
        show_toast(
            page=ft.context.page,
            message=loc.t(message_key),
            type=ToastType.WARNING,
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
            message=loc.t(message_key),
            type=toast_type,
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
                            content=ft.Row(
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
                                        size="lg" if not metrics.is_compact else "md",
                                        disabled=not can_decrement,
                                    ),
                                    ft.Container(
                                        width=speed_value_width,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=speed_control_gap,
                                            controls=[
                                                TangoText(
                                                    str(motor.speed_level),
                                                    variant="display",
                                                    size=speed_value_size,
                                                    text_align=ft.TextAlign.CENTER,
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
                                    TangoIconButton(
                                        icon=ft.Icons.ADD,
                                        icon_size=step_icon_size,
                                        on_click=on_increment_click,
                                        tooltip=loc.t("increment"),
                                        variant="primary",
                                        size="lg" if not metrics.is_compact else "md",
                                        disabled=not can_increment,
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
