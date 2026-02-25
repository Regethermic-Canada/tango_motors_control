from typing import Any
import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext
from utils.ui_scale import get_viewport_metrics


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)

    outer_pad = int(round((24 if metrics.compact else 40) * metrics.scale))
    section_spacing = int(round((20 if metrics.compact else 30) * metrics.scale))
    block_spacing = int(round((8 if metrics.compact else 10) * metrics.scale))
    title_size = int(round((24 if metrics.compact else 30) * metrics.scale))
    section_title_size = int(round((16 if metrics.compact else 20) * metrics.scale))
    value_size = int(round((14 if metrics.compact else 16) * metrics.scale))

    def on_timeout_change(e: Any) -> None:
        if e.control and hasattr(e.control, "value"):
            app_model.set_inactivity_timeout(float(e.control.value))

    timeout_label = ft.Text(
        loc.t("inactivity_timeout"),
        size=section_title_size,
        weight=ft.FontWeight.W_500,
    )
    timeout_value = ft.Text(
        f"{int(app_model.inactivity_limit)} {loc.t('seconds')}",
        size=value_size,
        color=ft.Colors.ON_SURFACE_VARIANT,
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

    return ft.Container(
        expand=True,
        padding=ft.Padding(outer_pad, outer_pad, outer_pad, outer_pad),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=section_spacing,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            loc.t("admin_settings"),
                            size=title_size,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                ft.Divider(),
                # Inactivity Timeout Section
                ft.Column(
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
            ],
        ),
    )
