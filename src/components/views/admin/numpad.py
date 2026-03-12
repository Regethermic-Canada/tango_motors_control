from collections.abc import Callable
import flet as ft
from flet.controls.control_event import Event
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton
from components.native.icon_button import TangoIconButton
from components.native.text import TangoText
from theme import colors, spacing
from theme.scale import get_viewport_metrics

ContainerHandler = ControlEventHandler[ft.Container] | None


def DigitButton(
    text: str,
    on_click: ContainerHandler,
    *,
    font_size: int,
    diameter: int,
) -> ft.Container:
    return ft.Container(
        width=diameter,
        height=diameter,
        alignment=ft.Alignment.CENTER,
        bgcolor=colors.SURFACE,
        border=ft.border.all(1, colors.OUTLINE),
        border_radius=diameter / 2,
        ink=True,
        on_click=on_click,
        content=TangoText(
            text,
            variant="subtitle",
            size=font_size,
            color=colors.TEXT,
            text_align=ft.TextAlign.CENTER,
        ),
    )


@ft.component
def NumericNumpad(
    on_digit_click: Callable[[str], None],
    on_backspace_click: Callable[[], None],
    on_clear_click: Callable[[], None],
) -> ft.Control:
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.62)

    numpad_width = min(
        450,
        max(320 if metrics.compact else 360, int(metrics.width * 0.48)),
    )
    row_spacing = int(round(spacing.MD * metrics.scale))
    digit_font_size = int(round(30 * metrics.scale))
    digit_diameter = int(round(64 * metrics.scale))
    action_icon_size = int(round(24 * metrics.scale))

    def handle_digit(digit: str) -> ContainerHandler:
        return lambda _: on_digit_click(digit)

    def handle_backspace(_: Event[IconButton]) -> None:
        on_backspace_click()

    def handle_clear(_: Event[IconButton]) -> None:
        on_clear_click()

    def digit(text: str) -> ft.Container:
        return DigitButton(
            text,
            handle_digit(text),
            font_size=digit_font_size,
            diameter=digit_diameter,
        )

    def action_button(
        icon: ft.IconData, on_click: ControlEventHandler[IconButton]
    ) -> ft.IconButton:
        return TangoIconButton(
            icon=icon,
            on_click=on_click,
            icon_size=action_icon_size,
            variant="surface",
            size="md",
        )

    return ft.Container(
        width=numpad_width,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=row_spacing,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        digit("1"),
                        digit("2"),
                        digit("3"),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        digit("4"),
                        digit("5"),
                        digit("6"),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        digit("7"),
                        digit("8"),
                        digit("9"),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        action_button(ft.Icons.BACKSPACE_OUTLINED, handle_backspace),
                        digit("0"),
                        action_button(ft.Icons.CLEAR_ALL, handle_clear),
                    ],
                ),
            ],
        ),
    )
