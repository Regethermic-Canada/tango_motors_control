from typing import Any
import flet as ft
from models.app_model import AppModel, MotorAction
from contexts.locale import LocaleContext
from components.shared.toast import ToastType, show_toast
from utils.ui_scale import get_viewport_metrics


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

    content_spacing = int(round((12 if metrics.compact else 14) * metrics.scale))
    speed_label_size = int(round((20 if metrics.compact else 20) * metrics.scale))
    speed_value_size = int(round((88 if metrics.compact else 80) * metrics.scale))
    speed_percent_size = int(round((24 if metrics.compact else 22) * metrics.scale))
    status_size = int(round((16 if metrics.compact else 14) * metrics.scale))
    button_text_size = int(round((20 if metrics.compact else 18) * metrics.scale))
    button_h_pad = int(round((22 if metrics.compact else 24) * metrics.scale))
    button_v_pad = int(round((14 if metrics.compact else 14) * metrics.scale))
    button_width = min(
        460,
        max(
            300 if metrics.compact else 280,
            int(metrics.width * (0.82 if metrics.compact else 0.5)),
        ),
    )
    step_icon_size = int(round((46 if metrics.compact else 40) * metrics.scale))
    step_spacing = int(round((32 if metrics.compact else 40) * metrics.scale))

    def on_toggle_click(_: Any) -> None:
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

    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        tight=True,
        spacing=content_spacing,
        controls=[
            ft.Text(
                loc.t("speed"),
                size=speed_label_size,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                value=str(model.speed_level),
                size=speed_value_size,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                value=f"{model.speed_percent}%",
                size=speed_percent_size,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Container(
                width=button_width,
                content=ft.FilledButton(
                    expand=True,
                    content=ft.Text(
                        loc.t("stop_motors") if is_running else loc.t("start_motors"),
                        size=button_text_size,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    icon=ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW,
                    on_click=on_toggle_click,
                    style=ft.ButtonStyle(
                        padding=ft.Padding(
                            button_h_pad,
                            button_v_pad,
                            button_h_pad,
                            button_v_pad,
                        )
                    ),
                ),
            ),
            ft.Text(
                value=(
                    loc.t("motor_status_running")
                    if is_running
                    else loc.t("motor_status_stopped")
                ),
                size=status_size,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=step_icon_size,
                        on_click=lambda _: model.decrement(),
                        tooltip=loc.t("decrement"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=step_icon_size,
                        on_click=lambda _: model.increment(),
                        tooltip=loc.t("increment"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=step_spacing,
            ),
        ],
    )
