import asyncio
from collections.abc import Callable

import flet as ft

from theme import animation, colors, typography

PASSCODE_LENGTH = 4
_SHAKE_POINTS = [
    ft.Offset(0.02, 0.01),
    ft.Offset(-0.02, -0.01),
    ft.Offset(0.02, -0.01),
    ft.Offset(-0.02, 0.01),
]


def _resolve_indicator_sizes(*, scale: float, is_compact: bool) -> tuple[int, int]:
    font_size = int(round((28 if is_compact else 34) * scale))
    letter_spacing = int(round((8 if is_compact else 10) * scale))
    return font_size, letter_spacing


def build_passcode_dots(
    passcode: str,
    *,
    length: int = PASSCODE_LENGTH,
) -> str:
    return "".join(
        "● " if index < len(passcode) else "○ " for index in range(length)
    ).strip()


def passcode_indicator_style(
    *,
    scale: float,
    is_compact: bool,
    is_active: bool,
) -> ft.TextStyle:
    font_size, letter_spacing = _resolve_indicator_sizes(
        scale=scale,
        is_compact=is_compact,
    )
    return typography.text_style(
        "headline",
        color=colors.PRIMARY if is_active else colors.OUTLINE,
        size=font_size,
        letter_spacing=letter_spacing,
    )


def PasscodeIndicator(
    *,
    passcode: str,
    scale: float,
    is_compact: bool,
    offset: ft.Offset | None = None,
) -> ft.Container:
    return ft.Container(
        offset=offset or ft.Offset(0, 0),
        animate_offset=animation.make(
            animation.AUTH_SHAKE_MS,
            animation.AUTH_SHAKE_CURVE,
        ),
        content=ft.Text(
            value=build_passcode_dots(passcode),
            style=passcode_indicator_style(
                scale=scale,
                is_compact=is_compact,
                is_active=bool(passcode),
            ),
            text_align=ft.TextAlign.CENTER,
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
