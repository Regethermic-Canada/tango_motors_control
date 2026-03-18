import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton

from services.app.overlay_registry import OverlayRole, cleanup_overlay, register_overlay
from theme import colors, radius, shadows
from theme.animation import (
    OVERLAY_MOUNT_FRAME_DELAY_S,
    TOAST_CLOSE_DELAY_S,
    TOAST_HIDDEN_OFFSET,
    TOAST_HIDDEN_OPACITY,
    TOAST_TRANSITION_CURVE,
    TOAST_TRANSITION_MS,
    TOAST_UPDATE_DELAY_S,
    TOAST_UPDATE_DIM_OPACITY,
    TOAST_UPDATE_MS,
    TOAST_VISIBLE_OFFSET,
    TOAST_VISIBLE_OPACITY,
    make,
)
from theme.scale import get_viewport_metrics

from .icon_button import TangoIconButton
from .text import TangoText

_TOAST_TRANSITION = make(TOAST_TRANSITION_MS, TOAST_TRANSITION_CURVE)
_TOAST_UPDATE_TRANSITION = make(TOAST_UPDATE_MS, TOAST_TRANSITION_CURVE)

ToastBuild = Callable[[], str]
ControlHandler = ControlEventHandler[IconButton] | None


class ToastType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class _ToastLayout:
    width: int
    top: int
    right: int
    close_tooltip: str
    is_compact: bool
    metrics_scale: float


@dataclass
class _ToastRuntime:
    container: ft.Container
    close_token: int
    expires_at: float | None


_active_toasts: dict[int, _ToastRuntime] = {}
_last_toast_at: dict[tuple[int, str], float] = {}


def TangoToast(
    *,
    message: str,
    type: ToastType,
    close_tooltip: str,
    is_compact: bool,
    metrics_scale: float,
    width: int,
    top: int,
    right: int,
    on_close: ControlHandler = None,
) -> ft.Container:
    toast_icon_size = int(round((22 if is_compact else 28) * metrics_scale))
    toast_text_size = int(round((14 if is_compact else 16) * metrics_scale))
    separator_height = int(round((18 if is_compact else 22) * metrics_scale))
    row_spacing = int(round((8 if is_compact else 12) * metrics_scale))
    pad_h_left = int(round((12 if is_compact else 16) * metrics_scale))
    pad_v = int(round((8 if is_compact else 10) * metrics_scale))
    pad_h_right = int(round((8 if is_compact else 12) * metrics_scale))

    palette = {
        ToastType.SUCCESS: (colors.SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE),
        ToastType.ERROR: (colors.ERROR, ft.Icons.ERROR_OUTLINE),
        ToastType.WARNING: (colors.WARNING_DARK, ft.Icons.WARNING_AMBER_OUTLINED),
        ToastType.INFO: (colors.PRIMARY, ft.Icons.INFO_OUTLINE),
    }
    bg_color, icon = palette.get(type, palette[ToastType.INFO])

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icon, color=colors.TEXT_INVERSE, size=toast_icon_size),
                ft.Container(
                    width=1,
                    height=separator_height,
                    bgcolor=colors.INVERSE_OUTLINE,
                    border_radius=999,
                ),
                TangoText(
                    message,
                    variant="body_strong",
                    color=colors.TEXT_INVERSE,
                    size=toast_text_size,
                    expand=True,
                ),
                TangoIconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip=close_tooltip,
                    on_click=on_close,
                    icon_size=int(round((14 if is_compact else 16) * metrics_scale)),
                    variant="inverse",
                    size="sm",
                ),
            ],
            tight=True,
            spacing=row_spacing,
        ),
        bgcolor=bg_color,
        padding=ft.Padding(pad_h_left, pad_v, pad_h_right, pad_v),
        border_radius=radius.TOAST,
        width=width,
        shadow=shadows.card_shadow(metrics_scale),
        animate_opacity=_TOAST_TRANSITION,
        animate_offset=_TOAST_TRANSITION,
        opacity=TOAST_HIDDEN_OPACITY,
        offset=TOAST_HIDDEN_OFFSET,
        top=top,
        right=right,
    )


def _update_toast_container(
    *,
    container: ft.Container,
    message: str,
    type: ToastType,
    layout: _ToastLayout,
    on_close: ControlHandler,
) -> None:
    next_container = TangoToast(
        message=message,
        type=type,
        close_tooltip=layout.close_tooltip,
        is_compact=layout.is_compact,
        metrics_scale=layout.metrics_scale,
        width=layout.width,
        top=layout.top,
        right=layout.right,
        on_close=on_close,
    )
    container.content = next_container.content
    container.bgcolor = next_container.bgcolor
    container.padding = next_container.padding
    container.border_radius = next_container.border_radius
    container.width = next_container.width
    container.shadow = next_container.shadow
    container.top = next_container.top
    container.right = next_container.right


def _is_active_toast(page_key: int, close_token: int) -> bool:
    current = _active_toasts.get(page_key)
    return current is not None and current.close_token == close_token


def _clear_existing_toast(page: ft.Page, page_key: int) -> None:
    existing = _active_toasts.get(page_key)
    if existing is None:
        return

    def finalize_cleanup() -> None:
        _active_toasts.pop(page_key, None)

    cleanup_overlay(
        page=page,
        role=OverlayRole.TOAST,
        control=existing.container,
        on_cleanup=finalize_cleanup,
    )


def _resolve_toast_layout(
    *,
    page: ft.Page,
    close_tooltip: str | None,
    position_top: int,
    position_right: int,
) -> _ToastLayout:
    metrics = get_viewport_metrics(page, min_scale=0.66)
    is_compact = metrics.is_compact
    resolved_top = getattr(page, "_tango_toast_top_offset", None)
    resolved_right = getattr(page, "_tango_toast_right_offset", None)
    width = min(
        280 if is_compact else 400,
        max(220, int(metrics.width - (position_right * 2) - 8)),
    )
    top = (
        int(resolved_top)
        if isinstance(resolved_top, int | float)
        else int(round(position_top * metrics.scale))
    )
    right = (
        int(resolved_right)
        if isinstance(resolved_right, int | float)
        else int(round(position_right * metrics.scale))
    )
    resolved_close_tooltip = (
        close_tooltip
        if close_tooltip is not None
        else getattr(page, "_tango_toast_close_tooltip", "Close")
    )
    return _ToastLayout(
        width=width,
        top=top,
        right=right,
        close_tooltip=resolved_close_tooltip,
        is_compact=is_compact,
        metrics_scale=metrics.scale,
    )


def _apply_open_state(runtime: _ToastRuntime) -> None:
    runtime.container.opacity = TOAST_VISIBLE_OPACITY
    runtime.container.offset = TOAST_VISIBLE_OFFSET


def _apply_closed_state(runtime: _ToastRuntime) -> None:
    runtime.container.opacity = TOAST_HIDDEN_OPACITY
    runtime.container.offset = TOAST_HIDDEN_OFFSET


def _resolve_expires_at(
    *,
    duration: float,
    expires_at: float | None,
) -> float | None:
    if expires_at is not None:
        return expires_at
    if duration <= 0:
        return None
    return time.monotonic() + duration


def _build_toast_runtime(
    *,
    message: str,
    type: ToastType,
    layout: _ToastLayout,
    on_close: ControlHandler,
    expires_at: float | None,
) -> _ToastRuntime:
    container = TangoToast(
        message=message,
        type=type,
        close_tooltip=layout.close_tooltip,
        is_compact=layout.is_compact,
        metrics_scale=layout.metrics_scale,
        width=layout.width,
        top=layout.top,
        right=layout.right,
        on_close=on_close,
    )
    return _ToastRuntime(
        container=container,
        close_token=0,
        expires_at=expires_at,
    )


def _schedule_toast_auto_hide(
    *,
    runtime: _ToastRuntime,
    page_key: int,
    close_token: int,
    close_toast: Callable[[], None],
) -> None:
    if runtime.expires_at is None:
        return

    expires_at = runtime.expires_at

    async def auto_hide() -> None:
        remaining_s = max(0.0, expires_at - time.monotonic())
        await asyncio.sleep(remaining_s)
        if not _is_active_toast(page_key, close_token):
            return
        close_toast()

    asyncio.create_task(auto_hide())


def _schedule_toast_update_animation(
    *,
    runtime: _ToastRuntime,
    page_key: int,
    close_token: int,
    update_content: Callable[[], None],
) -> None:
    async def animate_update() -> None:
        runtime.container.animate_opacity = _TOAST_UPDATE_TRANSITION
        runtime.container.opacity = TOAST_UPDATE_DIM_OPACITY
        runtime.container.update()

        await asyncio.sleep(TOAST_UPDATE_DELAY_S)
        if not _is_active_toast(page_key, close_token):
            return

        update_content()
        runtime.container.opacity = TOAST_VISIBLE_OPACITY
        runtime.container.update()

        await asyncio.sleep(TOAST_UPDATE_DELAY_S)
        if not _is_active_toast(page_key, close_token):
            return

        runtime.container.animate_opacity = _TOAST_TRANSITION

    asyncio.create_task(animate_update())


def _update_active_toast(
    *,
    page: ft.Page,
    runtime: _ToastRuntime,
    page_key: int,
    message: str,
    type: ToastType,
    duration: float,
    position_top: int,
    position_right: int,
    close_tooltip: str | None,
    build: ToastBuild | None,
    expires_at: float | None,
) -> None:
    layout = _resolve_toast_layout(
        page=page,
        close_tooltip=close_tooltip,
        position_top=position_top,
        position_right=position_right,
    )
    close_token = time.monotonic_ns()
    resolved_expires_at = _resolve_expires_at(
        duration=duration,
        expires_at=expires_at,
    )

    def close_toast() -> None:
        current = _active_toasts.get(page_key)
        if current is None or current.close_token != close_token:
            return
        if current.container not in page.overlay:
            return

        _apply_closed_state(current)
        current.container.update()

        def finalize_cleanup() -> None:
            _active_toasts.pop(page_key, None)

        cleanup_overlay(
            page=page,
            role=OverlayRole.TOAST,
            control=current.container,
            delay_s=TOAST_CLOSE_DELAY_S,
            is_current=lambda: _is_active_toast(page_key, close_token),
            on_cleanup=finalize_cleanup,
        )

    def refresh_toast() -> None:
        if build is None or not _is_active_toast(page_key, close_token):
            return
        current = _active_toasts.get(page_key)
        if current is None:
            return
        _update_active_toast(
            page=page,
            runtime=current,
            page_key=page_key,
            message=build(),
            type=type,
            duration=duration,
            position_top=position_top,
            position_right=position_right,
            close_tooltip=close_tooltip,
            build=build,
            expires_at=current.expires_at,
        )

    def apply_content_update() -> None:
        _update_toast_container(
            container=runtime.container,
            message=message,
            type=type,
            layout=layout,
            on_close=lambda _: close_toast(),
        )

    runtime.close_token = close_token
    runtime.expires_at = resolved_expires_at
    _apply_open_state(runtime)
    register_overlay(
        page,
        OverlayRole.TOAST,
        runtime.container,
        close_toast,
        refresh_callback=refresh_toast if build is not None else None,
    )
    _schedule_toast_update_animation(
        runtime=runtime,
        page_key=page_key,
        close_token=close_token,
        update_content=apply_content_update,
    )
    _schedule_toast_auto_hide(
        runtime=runtime,
        page_key=page_key,
        close_token=close_token,
        close_toast=close_toast,
    )


def _present_toast(
    *,
    page: ft.Page,
    message: str,
    type: ToastType,
    duration: float,
    position_top: int,
    position_right: int,
    close_tooltip: str | None,
    build: ToastBuild | None,
    animate_in: bool,
    insert_at: int | None,
    expires_at: float | None = None,
) -> None:
    page_key = id(page)
    current = _active_toasts.get(page_key)
    if current is not None and current.container in page.overlay:
        _update_active_toast(
            page=page,
            runtime=current,
            page_key=page_key,
            message=message,
            type=type,
            duration=duration,
            position_top=position_top,
            position_right=position_right,
            close_tooltip=close_tooltip,
            build=build,
            expires_at=expires_at,
        )
        return

    layout = _resolve_toast_layout(
        page=page,
        close_tooltip=close_tooltip,
        position_top=position_top,
        position_right=position_right,
    )
    _clear_existing_toast(page, page_key)

    close_token = time.monotonic_ns()
    resolved_expires_at = _resolve_expires_at(
        duration=duration,
        expires_at=expires_at,
    )

    def close_toast() -> None:
        current = _active_toasts.get(page_key)
        if current is None or current.close_token != close_token:
            return
        if current.container not in page.overlay:
            return

        _apply_closed_state(current)
        current.container.update()

        def finalize_cleanup() -> None:
            _active_toasts.pop(page_key, None)

        cleanup_overlay(
            page=page,
            role=OverlayRole.TOAST,
            control=current.container,
            delay_s=TOAST_CLOSE_DELAY_S,
            is_current=lambda: _is_active_toast(page_key, close_token),
            on_cleanup=finalize_cleanup,
        )

    def refresh_toast() -> None:
        if build is None or not _is_active_toast(page_key, close_token):
            return

        current = _active_toasts.get(page_key)
        next_insert_at = (
            page.overlay.index(current.container)
            if current is not None and current.container in page.overlay
            else None
        )
        _present_toast(
            page=page,
            message=build(),
            type=type,
            duration=duration,
            position_top=position_top,
            position_right=position_right,
            close_tooltip=close_tooltip,
            build=build,
            animate_in=False,
            insert_at=next_insert_at,
            expires_at=(
                current.expires_at if current is not None else resolved_expires_at
            ),
        )

    runtime = _build_toast_runtime(
        message=message,
        type=type,
        layout=layout,
        on_close=lambda _: close_toast(),
        expires_at=resolved_expires_at,
    )
    runtime.close_token = close_token
    _active_toasts[page_key] = runtime
    register_overlay(
        page,
        OverlayRole.TOAST,
        runtime.container,
        close_toast,
        refresh_callback=refresh_toast if build is not None else None,
    )

    resolved_insert_at = len(page.overlay) if insert_at is None else insert_at
    if animate_in:
        page.overlay.insert(resolved_insert_at, runtime.container)
        page.update()

        async def animate_in_task() -> None:
            await asyncio.sleep(OVERLAY_MOUNT_FRAME_DELAY_S)
            if not _is_active_toast(page_key, close_token):
                return
            current = _active_toasts[page_key]
            _apply_open_state(current)
            current.container.update()

        asyncio.create_task(animate_in_task())
    else:
        _apply_open_state(runtime)
        page.overlay.insert(resolved_insert_at, runtime.container)
        page.update()

    _schedule_toast_auto_hide(
        runtime=runtime,
        page_key=page_key,
        close_token=close_token,
        close_toast=close_toast,
    )


def show_toast(
    page: ft.Page,
    message: str | None = None,
    type: ToastType = ToastType.ERROR,
    duration: float = 3.0,
    position_top: int = 80,
    position_right: int = 20,
    close_tooltip: str | None = None,
    dedupe_window_s: float = 1.5,
    build: ToastBuild | None = None,
) -> None:
    if build is not None and message is not None:
        raise ValueError("show_toast() accepts either 'message' or 'build', not both.")
    if build is None and message is None:
        raise ValueError("show_toast() requires either 'message' or 'build'.")

    resolved_message = build() if build is not None else message
    if resolved_message is None:
        raise ValueError("show_toast() could not resolve a message.")

    page_key = id(page)
    toast_key = f"{type.value}:{resolved_message}"
    now = time.monotonic()
    last_shown = _last_toast_at.get((page_key, toast_key))
    if last_shown is not None and (now - last_shown) < dedupe_window_s:
        return
    _last_toast_at[(page_key, toast_key)] = now

    _present_toast(
        page=page,
        message=resolved_message,
        type=type,
        duration=duration,
        position_top=position_top,
        position_right=position_right,
        close_tooltip=close_tooltip,
        build=build,
        animate_in=True,
        insert_at=None,
    )
