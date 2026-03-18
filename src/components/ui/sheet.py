import flet as ft
from typing import Optional

from theme import colors, radius, spacing
from theme.scale import get_viewport_metrics
from .icon_button import TangoIconButton
from .text import TangoText


def TangoSheet(
    content: ft.Control,
    title: Optional[str] = None,
    show_drag_handle: bool = True,
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
        show_drag_handle: Whether to show the drag handle.
        dismissible: Whether the sheet can be dismissed by clicking outside.
        on_dismiss: Event handler called when the sheet is dismissed.
        padding: Padding for the content area.
        full_screen: Whether the sheet should be full screen height.
        expand: Whether the sheet should expand to almost full height and full width.
    """

    metrics = get_viewport_metrics(ft.context.page)

    # For full screen or expanded, we want to allow scrolling and large sizes
    sheet = ft.BottomSheet(
        content=ft.Container(),
        dismissible=dismissible,
        show_drag_handle=show_drag_handle,
        on_dismiss=on_dismiss,
        fullscreen=full_screen,
        scrollable=True,
        # Force full width on large screens by overriding constraints
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

    header = ft.Container(
        content=ft.Row(
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
        padding=ft.Padding(spacing.LG, spacing.MD, spacing.LG, spacing.MD),
        border=ft.Border(bottom=ft.BorderSide(1, colors.OUTLINE)),
    )

    # Calculate height if expand is True
    resolved_height = None
    if expand and not full_screen:
        resolved_height = int(metrics.height * 0.9)

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
        border_radius=ft.border_radius.only(
            top_left=radius.PANEL if not full_screen else 0,
            top_right=radius.PANEL if not full_screen else 0,
        ),
        expand=expand,
        height=resolved_height,
        width=metrics.width if (expand or full_screen) else None,
    )

    return sheet


def show_tango_sheet(
    page: ft.Page,
    content: ft.Control,
    title: Optional[str] = None,
    show_drag_handle: bool = True,
    dismissible: bool = True,
    on_dismiss: Optional[ft.ControlEventHandler[ft.DialogControl]] = None,
    padding: Optional[ft.Padding | int] = None,
    full_screen: bool = False,
    expand: bool = False,
) -> ft.BottomSheet:
    """
    Helper function to create and show a TangoSheet.
    """
    sheet = TangoSheet(
        content=content,
        title=title,
        show_drag_handle=show_drag_handle,
        dismissible=dismissible,
        on_dismiss=on_dismiss,
        padding=padding,
        full_screen=full_screen,
        expand=expand,
    )

    if sheet not in page.overlay:
        page.overlay.append(sheet)

    if hasattr(page, "open"):
        page.open(sheet)
    else:
        sheet.open = True
        page.update()

    return sheet
