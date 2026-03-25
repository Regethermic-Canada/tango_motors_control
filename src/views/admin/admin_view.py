import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from flet.controls.material.slider import Slider
from components.views.admin.admin_passcode_sheet import AdminPasscodeSheet
from components.ui.card import TangoCard
from components.ui.page import TangoPage
from components.ui.sheet import TangoSheet
from components.ui.text import TangoText
from components.ui.button import TangoButton
from contexts.settings import SettingsContext
from contexts.locale import LocaleContext
from theme import colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics, resolve_panel_width


@ft.component
def AdminView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    settings_service = ft.use_context(SettingsContext).current()
    is_passcode_sheet_open, set_is_passcode_sheet_open = ft.use_state(False)
    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        min_scale=0.7,
    )

    outer_pad = int(
        round((spacing.LG if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    section_spacing = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    block_spacing = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    section_title_size = int(round((18 if metrics.is_compact else 22) * metrics.scale))
    value_size = int(round((16 if metrics.is_compact else 18) * metrics.scale))
    card_width = resolve_panel_width(
        metrics,
        compact_fraction=0.82,
        regular_fraction=0.66,
        compact_min=500,
        regular_min=600,
        max_width=920,
        edge_padding=outer_pad,
    )
    card_padding = int(
        round((spacing.XL if metrics.is_compact else spacing.XXL) * metrics.scale)
    )
    slider_scale = max(1.08, metrics.scale * 1.08)
    slider_value_gap = max(4, int(round(6 * metrics.scale)))

    def on_timeout_change(e: Event[Slider]) -> None:
        value = e.control.value if e.control else None
        if isinstance(value, int | float):
            settings_service.set_inactivity_timeout(float(value))

    def on_default_speed_change(e: Event[Slider]) -> None:
        value = e.control.value if e.control else None
        if isinstance(value, int | float):
            settings_service.set_default_speed(int(round(value)))

    timeout_label = TangoText(
        loc.t("inactivity_timeout"),
        variant="subtitle",
        size=section_title_size,
    )
    timeout_value = TangoText(
        f"{int(settings_service.inactivity_timeout)} {loc.t('seconds')}",
        variant="caption",
        size=value_size,
        color=colors.TEXT_MUTED,
    )
    default_speed_label = TangoText(
        loc.t("default_speed"),
        variant="subtitle",
        size=section_title_size,
    )
    default_speed_value = TangoText(
        str(settings_service.default_speed),
        variant="caption",
        size=value_size,
        color=colors.TEXT_MUTED,
    )
    admin_passcode_label = TangoText(
        loc.t("change_admin_passcode"),
        variant="subtitle",
        size=section_title_size,
    )
    admin_passcode_description = TangoText(
        loc.t("admin_passcode_description"),
        variant="caption",
        size=value_size,
        color=colors.TEXT_MUTED,
    )

    timeout_header: ft.Control
    if metrics.is_compact:
        timeout_header = ft.Column(
            spacing=slider_value_gap,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[timeout_label, timeout_value],
        )
    else:
        timeout_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[timeout_label, timeout_value],
        )

    default_speed_header: ft.Control
    if metrics.is_compact:
        default_speed_header = ft.Column(
            spacing=slider_value_gap,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[default_speed_label, default_speed_value],
        )
    else:
        default_speed_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[default_speed_label, default_speed_value],
        )

    passcode_sheet_content = (
        AdminPasscodeSheet(on_close=lambda: set_is_passcode_sheet_open(False))
        if is_passcode_sheet_open
        else None
    )

    def on_change_admin_passcode_click(_: Event[Button]) -> None:
        set_is_passcode_sheet_open(True)

    return TangoPage(
        expand=True,
        padding=ft.Padding(outer_pad, outer_pad, outer_pad, outer_pad),
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=section_spacing,
                        controls=[
                            TangoCard(
                                width=card_width,
                                padding=ft.Padding(
                                    card_padding,
                                    card_padding,
                                    card_padding,
                                    card_padding,
                                ),
                                content=ft.Column(
                                    spacing=block_spacing,
                                    controls=[
                                        timeout_header,
                                        ft.Slider(
                                            min=10,
                                            max=150,
                                            divisions=14,
                                            label="{value}s",
                                            value=settings_service.inactivity_timeout,
                                            on_change=on_timeout_change,
                                            expand=True,
                                            scale=slider_scale,
                                        ),
                                        ft.Divider(height=section_spacing),
                                        default_speed_header,
                                        ft.Slider(
                                            min=settings_service.default_speed_min,
                                            max=settings_service.default_speed_max,
                                            divisions=settings_service.default_speed_max
                                            * 2,
                                            label="{value}",
                                            value=settings_service.default_speed,
                                            on_change=on_default_speed_change,
                                            expand=True,
                                            scale=slider_scale,
                                        ),
                                        ft.Divider(height=section_spacing),
                                        admin_passcode_label,
                                        admin_passcode_description,
                                        TangoButton(
                                            text=loc.t("change_admin_passcode"),
                                            variant="secondary",
                                            expand=True,
                                            size="lg",
                                            text_size=int(
                                                round(
                                                    (18 if metrics.is_compact else 19)
                                                    * metrics.scale
                                                )
                                            ),
                                            on_click=on_change_admin_passcode_click,
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                TangoSheet(
                    open=is_passcode_sheet_open,
                    title=loc.t("change_admin_passcode"),
                    content=passcode_sheet_content,
                    expand=True,
                    on_dismiss=lambda: set_is_passcode_sheet_open(False),
                ),
            ],
        ),
    )
