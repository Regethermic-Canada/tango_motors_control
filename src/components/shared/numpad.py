from typing import Any, Callable
import flet as ft


class DigitButton(ft.TextButton):
    def __init__(self, text: str, on_click: Callable[[Any], None]) -> None:
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.content = ft.Text(text, size=48, weight=ft.FontWeight.W_500)
        self.style = ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=ft.Padding(40, 40, 40, 40),
        )


@ft.component
def NumericNumpad(
    on_digit_click: Callable[[str], None],
    on_backspace_click: Callable[[], None],
    on_clear_click: Callable[[], None],
) -> ft.Control:

    def handle_digit(e: Any) -> None:
        digit = getattr(e.control, "text", "")
        on_digit_click(digit)

    def handle_backspace(e: Any) -> None:
        on_backspace_click()

    def handle_clear(e: Any) -> None:
        on_clear_click()

    return ft.Container(
        width=450,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        DigitButton("1", handle_digit),
                        DigitButton("2", handle_digit),
                        DigitButton("3", handle_digit),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        DigitButton("4", handle_digit),
                        DigitButton("5", handle_digit),
                        DigitButton("6", handle_digit),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        DigitButton("7", handle_digit),
                        DigitButton("8", handle_digit),
                        DigitButton("9", handle_digit),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.BACKSPACE_OUTLINED,
                            on_click=handle_backspace,
                            icon_size=48,
                        ),
                        DigitButton("0", handle_digit),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR_ALL,
                            on_click=handle_clear,
                            icon_size=48,
                        ),
                    ],
                ),
            ],
        ),
    )
