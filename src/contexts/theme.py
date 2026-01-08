from collections.abc import Callable
from dataclasses import dataclass
import flet as ft


@dataclass(frozen=True)
class ThemeContextValue:
    mode: ft.ThemeMode
    toggle_mode: Callable[[], None]


ThemeContext = ft.create_context(
    ThemeContextValue(
        mode=ft.ThemeMode.DARK,
        toggle_mode=lambda: None,
    )
)
