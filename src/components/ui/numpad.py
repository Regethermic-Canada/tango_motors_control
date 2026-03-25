from collections.abc import Callable
import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.icon_button import IconButton
from components.ui.icon_button import TangoIconButton
from components.ui.text import TangoText
from theme import colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics


def DigitButton(
    text: str,
    on_click: Callable[[Event[ft.Container]], None],
    *,
    font_size: int,
    diameter: int,
) -> ft.Container:
    return ft.Container(
        width=diameter,
        height=diameter,
        alignment=ft.Alignment.CENTER,
        bgcolor=colors.SURFACE,
        border=ft.Border.all(1, colors.OUTLINE),
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


def TangoNumpad(
    on_digit_click: Callable[[str], None],
    on_backspace_click: Callable[[], None],
    on_clear_click: Callable[[], None],
    *,
    scale_factor: float = 1.0,
) -> ft.Control:
    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        min_scale=0.62,
    )
    control_scale = max(0.72, metrics.scale * scale_factor)

    numpad_width = min(
        520,
        max(
            320 if metrics.is_compact else 440, int(metrics.width * 0.4 * scale_factor)
        ),
    )
    row_spacing = int(round(spacing.MD * control_scale))
    digit_font_size = int(round(30 * control_scale))
    digit_diameter = int(round(72 * control_scale))
    action_icon_size = int(round(24 * control_scale))

    def handle_digit(digit: str) -> Callable[[Event[ft.Container]], None]:
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
        icon: ft.IconData, on_click: Callable[[Event[IconButton]], None]
    ) -> ft.IconButton:
        return TangoIconButton(
            icon=icon,
            on_click=on_click,
            icon_size=action_icon_size,
            variant="surface",
            size="lg",
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
