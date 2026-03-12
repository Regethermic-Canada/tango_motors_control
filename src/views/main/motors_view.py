import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from components.native.button import TangoButton
from components.native.card import TangoCard
from components.native.icon_button import TangoIconButton
from components.native.tag import TangoTag, TagVariant
from components.native.text import TangoText
from components.native.toast import ToastType, show_toast
from models.app_model import AppModel, MotorAction
from contexts.locale import LocaleContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics


@ft.component
def MotorsView(model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(
        ft.context.page,
        base_width=960,
        base_height=540,
        min_scale=0.8,
    )
    is_running = model.is_motors_running

    content_spacing = int(round(spacing.SM * metrics.scale))
    panel_spacing = int(round(spacing.LG * metrics.scale))
    speed_label_size = int(round((15 if metrics.compact else 16) * metrics.scale))
    speed_value_size = int(round((72 if metrics.compact else 76) * metrics.scale))
    speed_percent_size = int(round((18 if metrics.compact else 20) * metrics.scale))
    button_text_size = int(round((16 if metrics.compact else 17) * metrics.scale))
    panel_width = min(
        640,
        max(
            360 if metrics.compact else 500,
            int(metrics.width * (0.8 if metrics.compact else 0.52)),
        ),
    )
    step_button_size = int(round((40 if metrics.compact else 48) * metrics.scale))
    step_icon_size = int(round((20 if metrics.compact else 22) * metrics.scale))
    step_spacing = int(
        round((spacing.SM if metrics.compact else spacing.LG) * metrics.scale)
    )
    speed_control_gap = int(
        round((spacing.XS if metrics.compact else spacing.SM) * metrics.scale)
    )
    speed_value_width = int(round((112 if metrics.compact else 144) * metrics.scale))
    speed_control_width = (step_button_size * 2) + speed_value_width + (
        step_spacing * 2
    )
    card_padding = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )

    status_variant: TagVariant = "success" if is_running else "secondary"
    status_label = (
        loc.t("motor_status_running") if is_running else loc.t("motor_status_stopped")
    )

    def on_toggle_click(_: Event[Button]) -> None:
        result = model.toggle_motors()

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
            close_tooltip=loc.t("close"),
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
                                        on_click=lambda _: model.decrement(),
                                        tooltip=loc.t("decrement"),
                                        variant="surface",
                                        size="lg" if not metrics.compact else "md",
                                    ),
                                    ft.Container(
                                        width=speed_value_width,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=speed_control_gap,
                                            controls=[
                                                TangoText(
                                                    str(model.speed_level),
                                                    variant="display",
                                                    size=speed_value_size,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                                TangoText(
                                                    f"{model.speed_percent}%",
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
                                        on_click=lambda _: model.increment(),
                                        tooltip=loc.t("increment"),
                                        variant="primary",
                                        size="lg" if not metrics.compact else "md",
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
                        size="lg" if not metrics.compact else "md",
                        text_size=button_text_size,
                        variant="surface" if is_running else "primary",
                    ),
                ),
            ],
        ),
    )
