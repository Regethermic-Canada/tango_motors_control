from dataclasses import dataclass
from typing import Literal

import flet as ft

from . import colors

FONT_FAMILY = "Manrope"
TextVariant = Literal[
    "display",
    "headline",
    "title",
    "subtitle",
    "body",
    "body_strong",
    "label",
    "caption",
    "overline",
]


@dataclass(frozen=True)
class TextSpec:
    size: int
    weight: ft.FontWeight
    color: str
    height: float = 1.2
    letter_spacing: float = 0


TEXT_VARIANTS: dict[TextVariant, TextSpec] = {
    "display": TextSpec(size=64, weight=ft.FontWeight.W_500, color=colors.TEXT),
    "headline": TextSpec(size=40, weight=ft.FontWeight.W_500, color=colors.TEXT),
    "title": TextSpec(size=32, weight=ft.FontWeight.W_500, color=colors.TEXT),
    "subtitle": TextSpec(size=24, weight=ft.FontWeight.W_500, color=colors.TEXT),
    "body": TextSpec(
        size=18, weight=ft.FontWeight.W_400, color=colors.TEXT, height=1.4
    ),
    "body_strong": TextSpec(
        size=18, weight=ft.FontWeight.W_500, color=colors.TEXT, height=1.4
    ),
    "label": TextSpec(size=18, weight=ft.FontWeight.W_500, color=colors.TEXT),
    "caption": TextSpec(size=14, weight=ft.FontWeight.W_400, color=colors.TEXT_MUTED),
    "overline": TextSpec(
        size=14,
        weight=ft.FontWeight.W_500,
        color=colors.TEXT_SOFT,
        letter_spacing=1.2,
    ),
}


def text_style(
    variant: TextVariant,
    *,
    color: str | None = None,
    size: int | None = None,
    weight: ft.FontWeight | None = None,
    letter_spacing: float | None = None,
) -> ft.TextStyle:
    spec = TEXT_VARIANTS[variant]
    return ft.TextStyle(
        font_family=FONT_FAMILY,
        size=size or spec.size,
        weight=weight or spec.weight,
        color=color or spec.color,
        height=spec.height,
        letter_spacing=(
            spec.letter_spacing if letter_spacing is None else letter_spacing
        ),
    )
