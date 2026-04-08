import flet as ft

from components.ui.card import TangoCard
from components.ui.tag import TangoTag, TagVariant
from components.ui.text import TangoText
from contexts.locale import LocaleContext
from services.motors.motor_service import MotorStatusSnapshot
from theme import colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics


def _format_metric(
    value: float | None,
    *,
    suffix: str,
    fallback: str,
    precision: int = 1,
) -> str:
    if value is None:
        return fallback
    return f"{value:.{precision}f} {suffix}"


def _build_metric_row(
    *,
    label: str,
    value: str,
    label_size: int,
    value_size: int,
    value_min_width: int,
) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                expand=True,
                content=ft.Text(
                    value=label,
                    style=TangoText(
                        "",
                        variant="caption",
                        size=label_size,
                        color=colors.TEXT_MUTED,
                    ).style,
                    no_wrap=True,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ),
            ft.Container(
                width=value_min_width,
                alignment=ft.Alignment.CENTER_RIGHT,
                content=ft.Text(
                    value=value,
                    style=TangoText(
                        "",
                        variant="body_strong",
                        size=value_size,
                        color=colors.TEXT,
                    ).style,
                    text_align=ft.TextAlign.RIGHT,
                    no_wrap=True,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ),
        ],
    )


def _chunk_controls(
    controls: list[ft.Control],
    *,
    chunk_size: int,
) -> list[list[ft.Control]]:
    return [
        controls[index : index + chunk_size]
        for index in range(0, len(controls), chunk_size)
    ]


@ft.component
def MotorStatusSheet(
    *,
    statuses: list[MotorStatusSnapshot],
    target_sec_per_tray: float,
    target_trays_per_minute: float,
) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        min_scale=0.72,
    )
    card_gap = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    content_padding = int(
        round((spacing.SM if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    card_padding = int(
        round((spacing.MD if metrics.is_compact else spacing.XL) * metrics.scale)
    )
    section_gap = int(
        round((spacing.MD if metrics.is_compact else spacing.LG) * metrics.scale)
    )
    row_gap = int(
        round((spacing.XS if metrics.is_compact else spacing.SM) * metrics.scale)
    )
    title_size = int(round((19 if metrics.is_compact else 22) * metrics.scale))
    value_size = int(round((16 if metrics.is_compact else 18) * metrics.scale))
    caption_size = int(round((14 if metrics.is_compact else 15) * metrics.scale))
    content_width = int(metrics.width * (0.9 if metrics.is_compact else 0.9))
    column_count = 1 if metrics.is_compact else min(2, max(1, len(statuses)))
    total_gap = card_gap * max(0, column_count - 1)
    card_width = max(320, int((content_width - total_gap) / column_count))
    value_min_width = int(round((116 if metrics.is_compact else 136) * metrics.scale))
    unavailable_value = loc.t("motor_status_not_available")

    def resolve_status(snapshot: MotorStatusSnapshot) -> tuple[str, TagVariant]:
        if snapshot.is_running:
            return (loc.t("motor_status_active"), "success")
        if snapshot.is_connected:
            return (loc.t("motor_status_stopped"), "secondary")
        return (loc.t("motor_status_disconnected"), "neutral")

    cards: list[ft.Control] = []
    for snapshot in statuses:
        status_label, status_variant = resolve_status(snapshot)
        measured_velocity_rad_s = snapshot.output_velocity_rad_s
        direction_label = (
            loc.t("motor_direction_forward")
            if snapshot.direction >= 0
            else loc.t("motor_direction_reverse")
        )
        cards.append(
            ft.Container(
                width=card_width,
                content=TangoCard(
                    padding=card_padding,
                    content=ft.Column(
                        spacing=section_gap,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    TangoText(
                                        f"{loc.t('motor_label')} {snapshot.motor_id}",
                                        variant="subtitle",
                                        size=title_size,
                                    ),
                                    TangoTag(status_label, variant=status_variant),
                                ],
                            ),
                            ft.Column(
                                spacing=row_gap,
                                controls=[
                                    _build_metric_row(
                                        label=loc.t("motor_direction"),
                                        value=direction_label,
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_temperature"),
                                        value=_format_metric(
                                            snapshot.temperature_c,
                                            suffix="°C",
                                            fallback=unavailable_value,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_velocity"),
                                        value=_format_metric(
                                            measured_velocity_rad_s,
                                            suffix="rad/s",
                                            fallback=unavailable_value,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_tray_time"),
                                        value=_format_metric(
                                            target_sec_per_tray,
                                            suffix=loc.t("seconds_per_tray_unit"),
                                            fallback=unavailable_value,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_tray_rate"),
                                        value=_format_metric(
                                            target_trays_per_minute,
                                            suffix=loc.t("trays_per_minute_unit"),
                                            fallback=unavailable_value,
                                            precision=1,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_torque"),
                                        value=_format_metric(
                                            snapshot.output_torque_nm,
                                            suffix="Nm",
                                            fallback=unavailable_value,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                    _build_metric_row(
                                        label=loc.t("motor_current"),
                                        value=_format_metric(
                                            snapshot.qaxis_current_a,
                                            suffix="A",
                                            fallback=unavailable_value,
                                        ),
                                        label_size=caption_size,
                                        value_size=value_size,
                                        value_min_width=value_min_width,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            )
        )

    rows: list[ft.Control] = [
        ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=card_gap,
            controls=row_controls,
        )
        for row_controls in _chunk_controls(cards, chunk_size=column_count)
    ]

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(
            content_padding, content_padding, content_padding, content_padding
        ),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=card_gap,
            controls=rows,
        ),
    )
