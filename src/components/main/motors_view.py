from typing import Any
import flet as ft
from models.app_model import AppModel, MotorAction
from contexts.locale import LocaleContext
from components.shared.toast import ToastType, show_toast


@ft.component
def MotorsView(model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    is_running = model.is_motors_running

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
        controls=[
            ft.Text(
                loc.t("speed"),
                size=20,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                value=str(model.speed_level),
                size=80,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                value=f"{model.speed_percent}%",
                size=22,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.FilledButton(
                content=loc.t("stop_motors") if is_running else loc.t("start_motors"),
                icon=ft.Icons.STOP if is_running else ft.Icons.PLAY_ARROW,
                on_click=on_toggle_click,
            ),
            ft.Text(
                value=(
                    loc.t("motor_status_running")
                    if is_running
                    else loc.t("motor_status_stopped")
                ),
                size=14,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.REMOVE,
                        icon_size=40,
                        on_click=lambda _: model.decrement(),
                        tooltip=loc.t("decrement"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_size=40,
                        on_click=lambda _: model.increment(),
                        tooltip=loc.t("increment"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=40,
            ),
        ],
    )
