import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.slider import Slider
from components.native.card import TangoCard
from components.native.page import TangoPage
from components.native.section_header import TangoSectionHeader
from components.native.text import TangoText
from models.app_model import AppModel
from contexts.locale import LocaleContext
from theme import colors, spacing
from theme.scale import get_viewport_metrics


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    outer_pad = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )
    section_spacing = int(
        round((spacing.LG if metrics.compact else spacing.XL) * metrics.scale)
    )
    block_spacing = int(round(spacing.XS * metrics.scale))
    title_size = int(round((22 if metrics.compact else 28) * metrics.scale))
    section_title_size = int(round((15 if metrics.compact else 18) * metrics.scale))
    value_size = int(round((14 if metrics.compact else 16) * metrics.scale))

    def on_timeout_change(e: Event[Slider]) -> None:
        value = e.control.value if e.control else None
        if isinstance(value, int | float):
            app_model.set_inactivity_timeout(float(value))

    timeout_label = TangoText(
        loc.t("inactivity_timeout"),
        variant="subtitle",
        size=section_title_size,
    )
    timeout_value = TangoText(
        f"{int(app_model.inactivity_limit)} {loc.t('seconds')}",
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

    return TangoPage(
        expand=True,
        padding=ft.Padding(outer_pad, outer_pad, outer_pad, outer_pad),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=section_spacing,
            controls=[
                TangoSectionHeader(
                    title=loc.t("admin_settings"),
                    subtitle=loc.t("application_config"),
                    title_size=title_size,
                ),
                TangoCard(
                    content=ft.Column(
                        spacing=block_spacing,
                        controls=[
                            timeout_header,
                            ft.Slider(
                                min=10,
                                max=150,
                                divisions=14,
                                label="{value}s",
                                value=app_model.inactivity_limit,
                                on_change=on_timeout_change,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
