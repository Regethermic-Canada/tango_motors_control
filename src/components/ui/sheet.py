import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional, cast

import flet as ft

from services.app.overlay_registry import (
    OverlayRole,
    cleanup_overlay,
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
from .icon_button import TangoIconButton
from .text import TangoText

_SHEET_TRANSITION = make(SHEET_TRANSITION_MS, SHEET_TRANSITION_CURVE)


@dataclass(frozen=True)
class _SheetLayout:
    panel_width: float | None
    panel_height: float | None
    panel_radius: ft.BorderRadius | int
    overlay_top_inset: float
    shadow: ft.BoxShadow
    header_padding: ft.Padding
    body_padding: ft.Padding | int


@dataclass
class _SheetRuntime:
    overlay: ft.Container
    anchor: ft.Container
    surface: ft.Container
    close_token: int


_active_sheets: dict[int, _SheetRuntime] = {}


def _trigger_dismiss(
    on_dismiss: Optional[ft.ControlEventHandler[ft.DialogControl]],
    control: ft.Control,
) -> None:
    if on_dismiss is None:
        return
    dismiss_handler = cast(Callable[[object], object], on_dismiss)
    dismiss_handler(ft.Event(name="dismiss", control=control))


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
    expand: bool,
) -> _SheetLayout:
    metrics = get_viewport_metrics(page, min_scale=0.7)
    top_band_height = int(round((68 if metrics.is_compact else 76) * metrics.scale))
    is_docked = expand and not full_screen
    panel_height = (
        metrics.height
        if full_screen
        else metrics.height - top_band_height if is_docked else None
    )
    panel_width = float(metrics.width) if (expand or full_screen) else None
    panel_radius: ft.BorderRadius | int = (
        0
        if (expand or full_screen)
        else ft.border_radius.only(top_left=radius.XXL, top_right=radius.XXL)
    )
    return _SheetLayout(
        panel_width=panel_width,
        panel_height=panel_height,
        panel_radius=panel_radius,
        overlay_top_inset=float(top_band_height),
        shadow=shadows.card_shadow(metrics.scale),
        header_padding=ft.Padding(spacing.LG, spacing.MD, spacing.LG, spacing.MD),
        body_padding=padding or spacing.LG,
    )


def _build_sheet_header(
    *,
    title: str | None,
    layout: _SheetLayout,
    request_close: Callable[[], None],
) -> ft.Container:
    title_control: ft.Control
    if title:
        title_control = TangoText(
            title,
            variant="title",
            size=22,
            expand=True,
        )
    else:
        title_control = ft.Container(expand=True)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        title_control,
                        TangoIconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: request_close(),
                            variant="surface",
                            size="md",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
            tight=True,
        ),
        padding=layout.header_padding,
        border=ft.Border(bottom=ft.BorderSide(1, colors.OUTLINE)),
    )


def _build_sheet_surface(
    *,
    content: ft.Control,
    header: ft.Control,
    layout: _SheetLayout,
    expand: bool,
) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                ft.Container(
                    content=content,
                    padding=layout.body_padding,
                    expand=expand,
                ),
            ],
            tight=not expand,
            spacing=0,
            expand=expand,
        ),
        bgcolor=colors.SURFACE,
        border_radius=layout.panel_radius,
        expand=expand,
        height=layout.panel_height,
        width=layout.panel_width,
        shadow=layout.shadow,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
    content: ft.Control,
    title: str | None,
    padding: ft.Padding | int | None,
    full_screen: bool,
    expand: bool,
    on_close: Callable[[], None],
) -> _SheetRuntime:
    layout = _resolve_sheet_layout(
        ft.context.page,
        padding=padding,
        full_screen=full_screen,
        expand=expand,
    )

    header = _build_sheet_header(
        title=title,
        layout=layout,
        request_close=on_close,
    )
    surface = _build_sheet_surface(
        content=content,
        header=header,
        layout=layout,
        expand=expand,
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
        close_token=0,
    )


def TangoSheet(
    content: ft.Control,
    *,
    title: Optional[str] = None,
    padding: Optional[ft.Padding | int] = None,
    full_screen: bool = False,
    expand: bool = False,
    on_close: Optional[Callable[[], None]] = None,
) -> _SheetRuntime:

    def request_close() -> None:
        if on_close is not None:
            on_close()

    return _build_sheet_runtime(
        content=content,
        title=title,
        padding=padding,
        full_screen=full_screen,
        expand=expand,
        on_close=request_close,
    )


def show_tango_sheet(
    page: ft.Page,
    content: ft.Control,
    title: Optional[str] = None,
    on_dismiss: Optional[ft.ControlEventHandler[ft.DialogControl]] = None,
    padding: Optional[ft.Padding | int] = None,
    full_screen: bool = False,
    expand: bool = False,
) -> ft.Container:
    page_key = id(page)
    _clear_existing_sheet(page, page_key)

    close_token = int(asyncio.get_running_loop().time() * 1_000_000)

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
            _trigger_dismiss(on_dismiss, current.overlay)

        cleanup_overlay(
            page=page,
            role=OverlayRole.SHEET,
            control=current.overlay,
            delay_s=SHEET_CLOSE_DELAY_S,
            is_current=lambda: _is_active_sheet(page_key, close_token),
            on_cleanup=finalize_cleanup,
        )

    runtime = TangoSheet(
        content=content,
        title=title,
        padding=padding,
        full_screen=full_screen,
        expand=expand,
        on_close=close_sheet,
    )
    runtime.close_token = close_token

    _active_sheets[page_key] = runtime
    register_overlay(page, OverlayRole.SHEET, runtime.overlay, close_sheet)

    insert_at = len(page.overlay)
    toast_overlay = get_overlay_control(page, OverlayRole.TOAST)
    if toast_overlay is not None and toast_overlay in page.overlay:
        insert_at = page.overlay.index(toast_overlay)
    page.overlay.insert(insert_at, runtime.overlay)
    page.update()

    async def animate_in() -> None:
        await asyncio.sleep(OVERLAY_MOUNT_FRAME_DELAY_S)
        if not _is_active_sheet(page_key, close_token):
            return
        current = _active_sheets[page_key]
        _apply_open_state(current)
        current.overlay.update()

    asyncio.create_task(animate_in())
    return runtime.overlay
