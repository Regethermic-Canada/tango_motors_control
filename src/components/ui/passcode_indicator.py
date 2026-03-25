import asyncio
from collections.abc import Callable

import flet as ft

from theme import animation, colors, radius

PASSCODE_LENGTH = 4
_SHAKE_POINTS = [
    ft.Offset(0.02, 0.01),
    ft.Offset(-0.02, -0.01),
    ft.Offset(0.02, -0.01),
    ft.Offset(-0.02, 0.01),
]


def _resolve_indicator_sizes(*, scale: float, is_compact: bool) -> tuple[int, int]:
    indicator_size = int(round((16 if is_compact else 18) * scale))
    indicator_spacing = int(round((14 if is_compact else 16) * scale))
    return indicator_size, indicator_spacing


def build_passcode_indicators(
    passcode: str,
    *,
    length: int = PASSCODE_LENGTH,
    scale: float,
    is_compact: bool,
) -> list[ft.Control]:
    indicator_size, _ = _resolve_indicator_sizes(
        scale=scale,
        is_compact=is_compact,
    )
    active_count = len(passcode)
    indicators: list[ft.Control] = []
    for index in range(length):
        is_active = index < active_count
        indicators.append(
            ft.Container(
                width=indicator_size,
                height=indicator_size,
                border_radius=radius.FULL,
                bgcolor=colors.PRIMARY if is_active else colors.SURFACE,
                border=ft.Border.all(
                    2,
                    colors.PRIMARY if is_active else colors.OUTLINE_STRONG,
                ),
            )
        )
    return indicators


def PasscodeIndicator(
    *,
    passcode: str,
    scale: float,
    is_compact: bool,
    offset: ft.Offset | None = None,
) -> ft.Container:
    _, indicator_spacing = _resolve_indicator_sizes(
        scale=scale,
        is_compact=is_compact,
    )
    return ft.Container(
        offset=offset or ft.Offset(0, 0),
        animate_offset=animation.make(
            animation.AUTH_SHAKE_MS,
            animation.AUTH_SHAKE_CURVE,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=indicator_spacing,
            controls=build_passcode_indicators(
                passcode,
                scale=scale,
                is_compact=is_compact,
            ),
        ),
    )


async def animate_passcode_shake(
    *,
    apply_offset: Callable[[ft.Offset], None],
) -> None:
    for _ in range(2):
        for point in _SHAKE_POINTS:
            apply_offset(point)
            await asyncio.sleep(0.03)

    apply_offset(ft.Offset(0, 0))
