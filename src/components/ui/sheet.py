import flet as ft
from typing import Optional

from theme import colors, spacing
from theme.scale import get_viewport_metrics
from .icon_button import TangoIconButton
from .text import TangoText


def TangoSheet(
    content: ft.Control,
    title: Optional[str] = None,
    dismissible: bool = True,
    on_dismiss: Optional[ft.ControlEventHandler[ft.DialogControl]] = None,
    padding: Optional[ft.Padding | int] = None,
    full_screen: bool = False,
    expand: bool = False,
) -> ft.BottomSheet:
    """
    A bottom sheet component styled for the Tango application.

    Args:
        content: The main content to display in the sheet.
        title: Optional title to display in the header.
        dismissible: Whether the sheet can be dismissed by clicking outside.
        on_dismiss: Event handler called when the sheet is dismissed.
        padding: Padding for the content area.
        full_screen: Whether the sheet should be full screen height.
        expand: Whether the sheet should expand to full width and dock under the header.
    """

    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)
    top_band_height = int(round((68 if metrics.is_compact else 76) * metrics.scale))
    is_docked = expand and not full_screen

    # Calculate exact height to stop right at the header bottom
    resolved_height = None
    if is_docked:
        resolved_height = metrics.height - top_band_height

    sheet = ft.BottomSheet(
        content=ft.Container(),
        dismissible=dismissible,
        # We always allow dragging to close the sheet for a natural feel
        draggable=True,
        # We hide the native handle to prevent it from covering the app header
        # and instead use our own custom one below.
        show_drag_handle=False,
        on_dismiss=on_dismiss,
        fullscreen=full_screen,
        scrollable=True,
        # Force full width on large screens by overriding Material 3 constraints
        size_constraints=(
            ft.BoxConstraints(
                min_width=metrics.width,
                max_width=metrics.width,
            )
            if (expand or full_screen)
            else None
        ),
    )

    header_controls: list[ft.Control] = []

    if title:
        header_controls.append(
            TangoText(
                title,
                variant="title",
                size=22,
                expand=True,
            )
        )
    else:
        header_controls.append(ft.Container(expand=True))

    def handle_close(e: ft.Event[ft.IconButton]) -> None:
        if hasattr(e.page, "close"):
            e.page.close(sheet)
        else:
            sheet.open = False
            e.page.update()

    # Custom draggable indicator bar
    drag_handle = ft.Container(
        width=40,
        height=4,
        bgcolor=colors.OUTLINE_STRONG,
        border_radius=2,
        margin=ft.margin.only(top=12, bottom=8),
    )

    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([drag_handle], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    controls=[
                        *header_controls,
                        TangoIconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=handle_close,
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
        padding=ft.Padding(spacing.LG, 0, spacing.LG, spacing.MD),
        border=ft.Border(bottom=ft.BorderSide(1, colors.OUTLINE)),
    )

    sheet.content = ft.Container(
        content=ft.Column(
            controls=[
                header,
                ft.Container(
                    content=content,
                    padding=padding or spacing.LG,
                    expand=expand,
                ),
            ],
            tight=not expand,
            spacing=0,
            expand=expand,
        ),
        bgcolor=colors.SURFACE,
        # Flat look when docked
        border_radius=0,
        expand=expand,
        height=resolved_height,
        width=metrics.width if (expand or full_screen) else None,
    )

    return sheet


def show_tango_sheet(
    page: ft.Page,
    content: ft.Control,
    title: Optional[str] = None,
    dismissible: bool = True,
    on_dismiss: Optional[ft.ControlEventHandler[ft.DialogControl]] = None,
    padding: Optional[ft.Padding | int] = None,
    full_screen: bool = False,
    expand: bool = False,
) -> ft.BottomSheet:
    """
    Helper function to create and show a TangoSheet.

    Args:
        page: The page where the sheet will be shown.
        content: The main content to display in the sheet.
        title: Optional title to display in the header.
        dismissible: Whether the sheet can be dismissed by clicking outside.
        on_dismiss: Event handler called when the sheet is dismissed.
        padding: Padding for the content area.
        full_screen: Whether the sheet should be full screen height.
        expand: Whether the sheet should expand to full width and dock under the header.
    """
    sheet = TangoSheet(
        content=content,
        title=title,
        dismissible=dismissible,
        on_dismiss=on_dismiss,
        padding=padding,
        full_screen=full_screen,
        expand=expand,
    )

    # Ensure the sheet is in the overlay to be part of the control tree
    if sheet not in page.overlay:
        page.overlay.append(sheet)

    if hasattr(page, "open"):
        page.open(sheet)
    else:
        sheet.open = True
        page.update()

    return sheet
