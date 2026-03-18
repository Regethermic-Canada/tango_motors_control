import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import flet as ft
from flet.controls.base_control import BaseControl


class OverlayRole(StrEnum):
    SHEET = "sheet"
    TOAST = "toast"


_PAGE_OVERLAYS_ATTR = "_tango_overlays"


@dataclass
class OverlayEntry:
    control: BaseControl
    close_callback: Callable[[], None]


OverlayRegistry = dict[OverlayRole, OverlayEntry]


def get_overlay_registry(page: ft.Page) -> OverlayRegistry:
    registry = getattr(page, _PAGE_OVERLAYS_ATTR, None)
    if isinstance(registry, dict):
        return registry
    registry = {}
    setattr(page, _PAGE_OVERLAYS_ATTR, registry)
    return registry


def register_overlay(
    page: ft.Page,
    role: OverlayRole,
    control: BaseControl,
    close_callback: Callable[[], None],
) -> None:
    get_overlay_registry(page)[role] = OverlayEntry(
        control=control,
        close_callback=close_callback,
    )


def unregister_overlay(page: ft.Page, role: OverlayRole) -> None:
    get_overlay_registry(page).pop(role, None)


def get_overlay_close_callback(
    page: ft.Page,
    role: OverlayRole,
) -> Callable[[], None] | None:
    entry = get_overlay_registry(page).get(role)
    if entry is None:
        return None
    callback = entry.close_callback
    return callback if callable(callback) else None


def get_overlay_control(page: ft.Page, role: OverlayRole) -> BaseControl | None:
    entry = get_overlay_registry(page).get(role)
    return entry.control if entry is not None else None


def remove_overlay_control(page: ft.Page, control: BaseControl) -> bool:
    if control not in page.overlay:
        return False
    page.overlay.remove(control)
    page.update()
    return True


def cleanup_overlay(
    *,
    page: ft.Page,
    role: OverlayRole,
    control: BaseControl,
    delay_s: float = 0.0,
    is_current: Callable[[], bool] | None = None,
    on_cleanup: Callable[[], None] | None = None,
) -> None:
    def finalize_cleanup() -> None:
        remove_overlay_control(page, control)
        unregister_overlay(page, role)
        if on_cleanup is not None:
            on_cleanup()

    if delay_s <= 0:
        finalize_cleanup()
        return

    async def remove_later() -> None:
        await asyncio.sleep(delay_s)
        if is_current is not None and not is_current():
            return
        finalize_cleanup()

    asyncio.create_task(remove_later())
