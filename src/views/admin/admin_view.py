import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.slider import Slider
from components.ui.card import TangoCard
from components.ui.page import TangoPage
from components.ui.text import TangoText
from components.ui.button import TangoButton
from components.ui.sheet import show_tango_sheet
from contexts.locale import LocaleContext
from contexts.settings import SettingsContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics


@ft.component
def AdminView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    settings_service = ft.use_context(SettingsContext).current()
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    outer_pad = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )
    section_spacing = int(round(spacing.LG * metrics.scale))
    block_spacing = int(round(spacing.XS * metrics.scale))
    section_title_size = int(round((15 if metrics.compact else 18) * metrics.scale))
    value_size = int(round((14 if metrics.compact else 16) * metrics.scale))
    card_width = min(
        760,
        max(360 if metrics.compact else 520, int(metrics.width * 0.58)),
    )
    card_padding = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )
    slider_scale = max(0.85, metrics.scale)

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

    timeout_header: ft.Control
    if metrics.compact:
        timeout_header = ft.Column(
            spacing=max(2, int(round(4 * metrics.scale))),
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[timeout_label, timeout_value],
        )
    else:
        timeout_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[timeout_label, timeout_value],
        )

    default_speed_header: ft.Control
    if metrics.compact:
        default_speed_header = ft.Column(
            spacing=max(2, int(round(4 * metrics.scale))),
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[default_speed_label, default_speed_value],
        )
    else:
        default_speed_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[default_speed_label, default_speed_value],
        )

    return TangoPage(
        expand=True,
        padding=ft.Padding(outer_pad, outer_pad, outer_pad, outer_pad),
        alignment=ft.Alignment.CENTER,
        content=ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
                                    divisions=settings_service.default_speed_max * 2,
                                    label="{value}",
                                    value=settings_service.default_speed,
                                    on_change=on_default_speed_change,
                                    expand=True,
                                    scale=slider_scale,
                                ),
                                ft.Divider(height=section_spacing),
                                TangoButton(
                                    text=loc.t("test_sheet"),
                                    variant="secondary",
                                    expand=True,
                                    on_click=lambda e: show_tango_sheet(
                                        e.page,
                                        content=TangoText(
                                            loc.t("test_content"),
                                        ),
                                        title=loc.t("test_sheet"),
                                        expand=True,
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    )
