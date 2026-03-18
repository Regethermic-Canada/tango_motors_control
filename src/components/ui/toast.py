import asyncio
import time
from dataclasses import dataclass
from enum import Enum
import flet as ft
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton

from services.app.overlay_registry import (
    OverlayRole,
    cleanup_overlay,
    register_overlay,
)
from .icon_button import TangoIconButton
from .text import TangoText
from theme import colors, radius, shadows
from theme.animation import (
    OVERLAY_MOUNT_FRAME_DELAY_S,
    TOAST_CLOSE_DELAY_S,
    TOAST_HIDDEN_OFFSET,
    TOAST_HIDDEN_OPACITY,
    TOAST_TRANSITION_CURVE,
    TOAST_TRANSITION_MS,
    TOAST_VISIBLE_OFFSET,
    TOAST_VISIBLE_OPACITY,
    make,
)
from theme.scale import get_viewport_metrics

_TOAST_TRANSITION = make(TOAST_TRANSITION_MS, TOAST_TRANSITION_CURVE)


class ToastType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class _ToastRuntime:
    container: ft.Container
    close_token: int


_active_toasts: dict[int, _ToastRuntime] = {}
_last_toast_at: dict[tuple[int, str], float] = {}
ControlHandler = ControlEventHandler[IconButton] | None


@dataclass(frozen=True)
class _ToastLayout:
    width: int
    top: int
    right: int
    close_tooltip: str
    is_compact: bool
    metrics_scale: float


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
            [
                ft.Icon(icon, color=colors.TEXT_INVERSE, size=toast_icon_size),
                ft.VerticalDivider(width=1, color=colors.INVERSE_OUTLINE),
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
        animate_opacity=TOAST_TRANSITION_MS,
        animate_offset=make(TOAST_TRANSITION_MS, TOAST_TRANSITION_CURVE),
        opacity=TOAST_HIDDEN_OPACITY,
        offset=TOAST_HIDDEN_OFFSET,
        top=top,
        right=right,
    )


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


def _build_toast_runtime(
    *,
    message: str,
    type: ToastType,
    layout: _ToastLayout,
    on_close: ControlHandler,
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
    container.animate_opacity = TOAST_TRANSITION_MS
    container.animate_offset = _TOAST_TRANSITION
    return _ToastRuntime(container=container, close_token=0)


def show_toast(
    page: ft.Page,
    message: str,
    type: ToastType = ToastType.ERROR,
    duration: float = 3.0,
    position_top: int = 80,
    position_right: int = 20,
    close_tooltip: str | None = None,
    dedupe_window_s: float = 1.5,
) -> None:
    layout = _resolve_toast_layout(
        page=page,
        close_tooltip=close_tooltip,
        position_top=position_top,
        position_right=position_right,
    )
    page_key = id(page)
    toast_key = f"{type.value}:{message}"
    now = time.monotonic()
    last_shown = _last_toast_at.get((page_key, toast_key))
    if last_shown is not None and (now - last_shown) < dedupe_window_s:
        return
    _last_toast_at[(page_key, toast_key)] = now

    _clear_existing_toast(page, page_key)
    close_token = int(time.monotonic_ns())

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

    runtime = _build_toast_runtime(
        message=message,
        type=type,
        layout=layout,
        on_close=lambda _: close_toast(),
    )
    runtime.close_token = close_token
    _active_toasts[page_key] = runtime
    register_overlay(page, OverlayRole.TOAST, runtime.container, close_toast)
    page.overlay.append(runtime.container)
    page.update()

    async def animate_in() -> None:
        await asyncio.sleep(OVERLAY_MOUNT_FRAME_DELAY_S)
        if not _is_active_toast(page_key, close_token):
            return
        current = _active_toasts[page_key]
        _apply_open_state(current)
        current.container.update()

    async def auto_hide() -> None:
        await asyncio.sleep(duration)
        close_toast()

    asyncio.create_task(animate_in())
    asyncio.create_task(auto_hide())
