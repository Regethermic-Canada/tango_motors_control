import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from services.app.overlay_registry import (
    OverlayRole,
    cleanup_overlay,
    get_overlay_close_callback,
    get_overlay_control,
    register_overlay,
)
from theme import colors, radius, shadows, spacing
from theme.animation import (
    OVERLAY_MOUNT_FRAME_DELAY_S,
    SHEET_ANCHOR_CLOSED_OFFSET,
    SHEET_ANCHOR_OPEN_OFFSET,
    SHEET_CLOSE_DELAY_S,
    SHEET_SURFACE_CLOSED_OFFSET,
    SHEET_SURFACE_CLOSED_OPACITY,
    SHEET_SURFACE_CLOSED_SCALE,
    SHEET_SURFACE_OPEN_OFFSET,
    SHEET_SURFACE_OPEN_OPACITY,
    SHEET_SURFACE_OPEN_SCALE,
    SHEET_TRANSITION_CURVE,
    SHEET_TRANSITION_MS,
    make,
)
from theme.scale import get_viewport_metrics

from .icon_button import IconButtonSize, TangoIconButton
from .text import TangoText

_SHEET_TRANSITION = make(SHEET_TRANSITION_MS, SHEET_TRANSITION_CURVE)

__all__ = ["TangoSheet"]

_SheetBuild = Callable[[], tuple[str | None, ft.Control]]


@dataclass(frozen=True)
class _SheetLayout:
    panel_width: float | None
    panel_height: float | None
    panel_radius: ft.BorderRadius | int
    overlay_top_inset: float
    shadow: ft.BoxShadow
    header_padding: ft.Padding
    header_title_size: int
    close_button_size: IconButtonSize
    body_padding: ft.Padding | int


@dataclass
class _SheetRuntime:
    overlay: ft.Container
    anchor: ft.Container
    surface: ft.Container
    header: ft.Container
    title_slot: ft.Container
    close_button: ft.IconButton
    body: ft.Container
    close_token: int


_active_sheets: dict[int, _SheetRuntime] = {}


def _trigger_dismiss(
    on_dismiss: Callable[[], None] | None,
) -> None:
    if on_dismiss is None:
        return
    on_dismiss()


def _is_active_sheet(page_key: int, close_token: int) -> bool:
    current = _active_sheets.get(page_key)
    return current is not None and current.close_token == close_token


def _clear_existing_sheet(page: ft.Page, page_key: int) -> None:
    existing = _active_sheets.get(page_key)
    if existing is None:
        return

    def finalize_cleanup() -> None:
        _active_sheets.pop(page_key, None)

    cleanup_overlay(
        page=page,
        role=OverlayRole.SHEET,
        control=existing.overlay,
        on_cleanup=finalize_cleanup,
    )


def _resolve_sheet_layout(
    page: ft.Page,
    *,
    padding: ft.Padding | int | None,
    full_screen: bool,
) -> _SheetLayout:
    metrics = get_viewport_metrics(page, min_scale=0.7)
    top_band_height = int(round((68 if metrics.is_compact else 76) * metrics.scale))
    is_docked = not full_screen
    panel_height = (
        metrics.height
        if full_screen
        else metrics.height - top_band_height if is_docked else None
    )
    panel_width = float(metrics.width)
    panel_radius: ft.BorderRadius | int = (
        0
        if full_screen or is_docked
        else ft.border_radius.only(top_left=radius.XXL, top_right=radius.XXL)
    )
    return _SheetLayout(
        panel_width=panel_width,
        panel_height=panel_height,
        panel_radius=panel_radius,
        overlay_top_inset=float(top_band_height),
        shadow=shadows.card_shadow(metrics.scale),
        header_padding=ft.Padding(
            spacing.MD,
            spacing.SM if metrics.is_compact else spacing.MD,
            spacing.MD,
            spacing.SM if metrics.is_compact else spacing.MD,
        ),
        header_title_size=int(
            round((16 if metrics.is_compact else 18) * metrics.scale)
        ),
        close_button_size="sm" if metrics.is_compact else "md",
        body_padding=padding or spacing.LG,
    )


def _build_sheet_title_control(title: str | None, *, size: int) -> ft.Control:
    if title is None:
        return ft.Container(expand=True)
    return TangoText(
        title,
        variant="title",
        size=size,
        expand=True,
    )


def _build_sheet_header(
    *,
    title: str | None,
    layout: _SheetLayout,
    close_tooltip: str | None,
    request_close: Callable[[], None],
) -> tuple[ft.Container, ft.Container, ft.IconButton]:
    title_slot = ft.Container(
        content=_build_sheet_title_control(title, size=layout.header_title_size),
        expand=True,
    )
    close_button = TangoIconButton(
        icon=ft.Icons.CLOSE,
        tooltip=close_tooltip,
        on_click=lambda _: request_close(),
        variant="surface",
        size=layout.close_button_size,
    )

    return (
        ft.Container(
            content=ft.Row(
                controls=[
                    title_slot,
                    close_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=layout.header_padding,
            border=ft.Border(bottom=ft.BorderSide(1, colors.OUTLINE)),
        ),
        title_slot,
        close_button,
    )


def _build_sheet_surface(
    *,
    body: ft.Container,
    header: ft.Container,
    layout: _SheetLayout,
) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                body,
            ],
            spacing=0,
            tight=False,
            expand=True,
        ),
        bgcolor=colors.SURFACE,
        border_radius=layout.panel_radius,
        expand=True,
        height=layout.panel_height,
        width=layout.panel_width,
        shadow=layout.shadow,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


def _build_sheet_body_content(
    *,
    content: ft.Control,
    scrollable: bool,
) -> ft.Control:
    if scrollable:
        return ft.ListView(
            controls=[
                ft.Container(
                    alignment=ft.Alignment.TOP_CENTER,
                    content=content,
                )
            ],
            expand=True,
            spacing=0,
        )

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=content,
    )


def _build_sheet_body(
    *,
    content: ft.Control,
    layout: _SheetLayout,
    scrollable: bool,
) -> ft.Container:
    return ft.Container(
        content=_build_sheet_body_content(
            content=content,
            scrollable=scrollable,
        ),
        padding=layout.body_padding,
        expand=True,
        alignment=ft.Alignment.TOP_CENTER,
    )


def _apply_open_state(runtime: _SheetRuntime) -> None:
    runtime.anchor.offset = SHEET_ANCHOR_OPEN_OFFSET
    runtime.surface.opacity = SHEET_SURFACE_OPEN_OPACITY
    runtime.surface.scale = SHEET_SURFACE_OPEN_SCALE
    runtime.surface.offset = SHEET_SURFACE_OPEN_OFFSET


def _apply_closed_state(runtime: _SheetRuntime) -> None:
    runtime.anchor.offset = SHEET_ANCHOR_CLOSED_OFFSET
    runtime.surface.opacity = SHEET_SURFACE_CLOSED_OPACITY
    runtime.surface.scale = SHEET_SURFACE_CLOSED_SCALE
    runtime.surface.offset = SHEET_SURFACE_CLOSED_OFFSET


def _build_sheet_runtime(
    *,
    page: ft.Page,
    content: ft.Control,
    title: str | None,
    padding: ft.Padding | int | None,
    full_screen: bool,
    scrollable: bool,
    on_close: Callable[[], None],
) -> _SheetRuntime:
    layout = _resolve_sheet_layout(
        page,
        padding=padding,
        full_screen=full_screen,
    )
    header, title_slot, close_button = _build_sheet_header(
        title=title,
        layout=layout,
        close_tooltip=getattr(page, "_tango_sheet_close_tooltip", "Close"),
        request_close=on_close,
    )
    body = _build_sheet_body(
        content=content,
        layout=layout,
        scrollable=scrollable,
    )
    surface = _build_sheet_surface(
        body=body,
        header=header,
        layout=layout,
    )
    surface.opacity = SHEET_SURFACE_CLOSED_OPACITY
    surface.scale = SHEET_SURFACE_CLOSED_SCALE
    surface.offset = SHEET_SURFACE_CLOSED_OFFSET
    surface.animate_opacity = _SHEET_TRANSITION
    surface.animate_scale = _SHEET_TRANSITION
    surface.animate_offset = None

    anchor = ft.Container(
        content=surface,
        offset=SHEET_ANCHOR_CLOSED_OFFSET,
        animate_offset=_SHEET_TRANSITION,
    )
    overlay = ft.Container(
        left=0,
        top=layout.overlay_top_inset,
        right=0,
        bottom=0,
        alignment=ft.Alignment.BOTTOM_CENTER,
        content=anchor,
    )
    return _SheetRuntime(
        overlay=overlay,
        anchor=anchor,
        surface=surface,
        header=header,
        title_slot=title_slot,
        close_button=close_button,
        body=body,
        close_token=0,
    )


def _update_sheet_runtime(
    runtime: _SheetRuntime,
    *,
    page: ft.Page,
    content: ft.Control,
    title: str | None,
    padding: ft.Padding | int | None,
    full_screen: bool,
    scrollable: bool,
) -> None:
    layout = _resolve_sheet_layout(
        page,
        padding=padding,
        full_screen=full_screen,
    )
    runtime.overlay.top = layout.overlay_top_inset
    runtime.surface.height = layout.panel_height
    runtime.surface.width = layout.panel_width
    runtime.surface.border_radius = layout.panel_radius
    runtime.surface.shadow = layout.shadow
    runtime.surface.expand = True
    runtime.header.padding = layout.header_padding
    runtime.body.padding = layout.body_padding
    runtime.body.content = _build_sheet_body_content(
        content=content,
        scrollable=scrollable,
    )
    runtime.body.expand = True
    runtime.title_slot.content = _build_sheet_title_control(
        title,
        size=layout.header_title_size,
    )
    runtime.close_button.tooltip = getattr(page, "_tango_sheet_close_tooltip", "Close")
    runtime.overlay.update()


def _create_sheet_runtime(
    page: ft.Page,
    content: ft.Control,
    *,
    title: str | None = None,
    padding: ft.Padding | int | None = None,
    full_screen: bool = False,
    scrollable: bool = False,
    on_close: Callable[[], None] | None = None,
) -> _SheetRuntime:
    def request_close() -> None:
        if on_close is not None:
            on_close()

    return _build_sheet_runtime(
        page=page,
        content=content,
        title=title,
        padding=padding,
        full_screen=full_screen,
        scrollable=scrollable,
        on_close=request_close,
    )


def _resolve_sheet_insert_index(page: ft.Page, insert_at: int | None) -> int:
    if insert_at is not None:
        return insert_at

    next_insert_at = len(page.overlay)
    toast_overlay = get_overlay_control(page, OverlayRole.TOAST)
    if toast_overlay is not None and toast_overlay in page.overlay:
        next_insert_at = page.overlay.index(toast_overlay)
    return next_insert_at


def _present_sheet(
    *,
    page: ft.Page,
    content: ft.Control,
    title: str | None,
    on_dismiss: Callable[[], None] | None,
    padding: ft.Padding | int | None,
    full_screen: bool,
    scrollable: bool,
    build: _SheetBuild | None,
    animate_in: bool,
    insert_at: int | None,
) -> ft.Container:
    page_key = id(page)
    current = _active_sheets.get(page_key)
    if current is not None and current.overlay in page.overlay:
        _update_sheet_runtime(
            current,
            page=page,
            content=content,
            title=title,
            padding=padding,
            full_screen=full_screen,
            scrollable=scrollable,
        )
        return current.overlay

    _clear_existing_sheet(page, page_key)

    close_token = time.monotonic_ns()

    def close_sheet() -> None:
        current = _active_sheets.get(page_key)
        if current is None or current.close_token != close_token:
            return
        if current.overlay not in page.overlay:
            return

        _apply_closed_state(current)
        current.overlay.update()

        def finalize_cleanup() -> None:
            _active_sheets.pop(page_key, None)
            _trigger_dismiss(on_dismiss)

        cleanup_overlay(
            page=page,
            role=OverlayRole.SHEET,
            control=current.overlay,
            delay_s=SHEET_CLOSE_DELAY_S,
            is_current=lambda: _is_active_sheet(page_key, close_token),
            on_cleanup=finalize_cleanup,
        )

    def refresh_sheet() -> None:
        if build is None or not _is_active_sheet(page_key, close_token):
            return

        current = _active_sheets.get(page_key)
        next_insert_at = (
            page.overlay.index(current.overlay)
            if current is not None and current.overlay in page.overlay
            else None
        )
        next_title, next_content = build()
        _present_sheet(
            page=page,
            content=next_content,
            title=next_title,
            on_dismiss=on_dismiss,
            padding=padding,
            full_screen=full_screen,
            scrollable=scrollable,
            build=build,
            animate_in=False,
            insert_at=next_insert_at,
        )

    runtime = _create_sheet_runtime(
        page=page,
        content=content,
        title=title,
        padding=padding,
        full_screen=full_screen,
        scrollable=scrollable,
        on_close=close_sheet,
    )
    runtime.close_token = close_token
    _active_sheets[page_key] = runtime
    register_overlay(
        page,
        OverlayRole.SHEET,
        runtime.overlay,
        close_sheet,
        refresh_callback=refresh_sheet if build is not None else None,
    )

    resolved_insert_at = _resolve_sheet_insert_index(page, insert_at)
    if animate_in:
        page.overlay.insert(resolved_insert_at, runtime.overlay)
        page.update()

        async def animate_in_task() -> None:
            await asyncio.sleep(OVERLAY_MOUNT_FRAME_DELAY_S)
            if not _is_active_sheet(page_key, close_token):
                return
            current = _active_sheets[page_key]
            _apply_open_state(current)
            current.overlay.update()

        asyncio.create_task(animate_in_task())
    else:
        _apply_open_state(runtime)
        page.overlay.insert(resolved_insert_at, runtime.overlay)
        page.update()

    return runtime.overlay


def _show_sheet(
    page: ft.Page,
    content: ft.Control | None = None,
    title: str | None = None,
    on_dismiss: Callable[[], None] | None = None,
    padding: ft.Padding | int | None = None,
    full_screen: bool = False,
    scrollable: bool = False,
    build: _SheetBuild | None = None,
) -> ft.Container:
    if build is not None and (content is not None or title is not None):
        raise ValueError(
            "_show_sheet() accepts either static content/title or 'build', not both."
        )
    if build is not None:
        title, content = build()
    if content is None:
        raise ValueError("_show_sheet() requires either 'content' or 'build'.")

    return _present_sheet(
        page=page,
        content=content,
        title=title,
        on_dismiss=on_dismiss,
        padding=padding,
        full_screen=full_screen,
        scrollable=scrollable,
        build=build,
        animate_in=True,
        insert_at=None,
    )


@ft.component
def TangoSheet(
    *,
    open: bool,
    content: ft.Control | None = None,
    title: str | None = None,
    on_dismiss: Callable[[], None] | None = None,
    padding: ft.Padding | int | None = None,
    full_screen: bool = False,
    scrollable: bool = False,
) -> ft.Control:
    page = ft.context.page

    def _sync_sheet_overlay() -> None:
        close_sheet = get_overlay_close_callback(page, OverlayRole.SHEET)
        if not open:
            if callable(close_sheet):
                close_sheet()
            return
        if content is None:
            return

        _show_sheet(
            page=page,
            content=content,
            title=title,
            on_dismiss=on_dismiss,
            padding=padding,
            full_screen=full_screen,
            scrollable=scrollable,
        )

    def _cleanup_sheet_overlay() -> None:
        close_sheet = get_overlay_close_callback(page, OverlayRole.SHEET)
        if callable(close_sheet):
            close_sheet()

    ft.use_effect(
        _sync_sheet_overlay,
        [
            open,
            title,
            content,
            padding,
            full_screen,
            scrollable,
        ],
    )
    ft.on_unmounted(_cleanup_sheet_overlay)

    return ft.Container(
        width=0,
        height=0,
        visible=False,
    )
