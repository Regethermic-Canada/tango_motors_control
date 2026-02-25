from typing import Any, Callable
import flet as ft
from utils.ui_scale import get_viewport_metrics


class DigitButton(ft.TextButton):
    def __init__(
        self,
        text: str,
        on_click: Callable[[Any], None],
        *,
        font_size: int,
        padding: int,
    ) -> None:
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.content = ft.Text(text, size=font_size, weight=ft.FontWeight.W_500)
        self.style = ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.Padding(padding, padding, padding, padding),
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
    row_spacing = int(round(20 * metrics.scale))
    digit_font_size = int(round(48 * metrics.scale))
    digit_padding = int(round(40 * metrics.scale))
    action_icon_size = int(round(48 * metrics.scale))

    def handle_digit(e: Any) -> None:
        digit = getattr(e.control, "text", "")
        on_digit_click(digit)

    def handle_backspace(e: Any) -> None:
        on_backspace_click()

    def handle_clear(e: Any) -> None:
        on_clear_click()

    def digit(text: str) -> DigitButton:
        return DigitButton(
            text,
            handle_digit,
            font_size=digit_font_size,
            padding=digit_padding,
        )

    def action_button(
        icon: ft.IconData, on_click: Callable[[Any], None]
    ) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            on_click=on_click,
            icon_size=action_icon_size,
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
