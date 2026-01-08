from collections.abc import Callable
from dataclasses import dataclass
import flet as ft


@dataclass(frozen=True)
class RouteContextValue:
    route: str
    navigate: Callable[[str], None]


RouteContext = ft.create_context(
    RouteContextValue(
        route="/",
        navigate=lambda _: None,
    )
)
