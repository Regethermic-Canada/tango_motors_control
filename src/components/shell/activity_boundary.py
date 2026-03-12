from collections.abc import Callable

import flet as ft


def ActivityBoundary(
    *,
    content: ft.Control,
    on_activity: Callable[[], None],
) -> ft.GestureDetector:
    return ft.GestureDetector(
        content=content,
        drag_interval=0,
        on_tap_down=lambda _: on_activity(),
        on_pan_down=lambda _: on_activity(),
        on_pan_update=lambda _: on_activity(),
        on_scroll=lambda _: on_activity(),
        on_long_press_down=lambda _: on_activity(),
        on_secondary_tap_down=lambda _: on_activity(),
    )
