from collections.abc import Callable

import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.slider import Slider


def _resolve_slider_value(event: Event[Slider]) -> float | None:
    value = event.control.value if event.control else None
    if isinstance(value, int | float):
        return float(value)
    return None


@ft.component
def TangoSlider(
    *,
    value: float,
    set_value: Callable[[float], None],
    on_commit: Callable[[float], None],
    min: int | float,
    max: int | float,
    divisions: int | None = None,
    label: str | None = None,
    scale: float | None = None,
    expand: bool = True,
) -> ft.Control:
    def on_change(event: Event[Slider]) -> None:
        next_value = _resolve_slider_value(event)
        if next_value is None:
            return
        set_value(next_value)

    def on_change_end(event: Event[Slider]) -> None:
        committed_value = _resolve_slider_value(event)
        if committed_value is None:
            return
        set_value(committed_value)
        on_commit(committed_value)

    return ft.Slider(
        min=min,
        max=max,
        divisions=divisions,
        label=label,
        value=value,
        on_change=on_change,
        on_change_end=on_change_end,
        expand=expand,
        scale=scale,
    )
