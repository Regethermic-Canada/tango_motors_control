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
) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            TangoText(
                label,
                variant="caption",
                size=label_size,
                color=colors.TEXT_MUTED,
            ),
            TangoText(
                value,
                variant="body_strong",
                size=value_size,
                color=colors.TEXT,
                text_align=ft.TextAlign.RIGHT,
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
def MotorStatusSheet(*, statuses: list[MotorStatusSnapshot]) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(
        ft.context.page,
        area=ViewportArea.CONTENT,
        min_scale=0.72,
    )
    card_gap = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    card_padding = int(
        round((spacing.SM if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    title_size = int(round((18 if metrics.is_compact else 20) * metrics.scale))
    value_size = int(round((15 if metrics.is_compact else 16) * metrics.scale))
    caption_size = int(round((13 if metrics.is_compact else 14) * metrics.scale))
    content_width = int(metrics.width * (0.94 if metrics.is_compact else 0.96))
    column_count = 1 if metrics.is_compact else min(2, max(1, len(statuses)))
    total_gap = card_gap * max(0, column_count - 1)
    card_width = max(320, int((content_width - total_gap) / column_count))
    unavailable_value = loc.t("motor_status_not_available")

    def resolve_status(snapshot: MotorStatusSnapshot) -> tuple[str, TagVariant]:
        if snapshot.is_active:
            return (loc.t("motor_status_active"), "success")
        if snapshot.is_connected:
            return (loc.t("motor_status_connected"), "secondary")
        return (loc.t("motor_status_disconnected"), "neutral")

    cards: list[ft.Control] = []
    for snapshot in statuses:
        status_label, status_variant = resolve_status(snapshot)
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
                        spacing=card_gap,
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
                            _build_metric_row(
                                label=loc.t("motor_direction"),
                                value=direction_label,
                                label_size=caption_size,
                                value_size=value_size,
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
                            ),
                            _build_metric_row(
                                label=loc.t("motor_velocity"),
                                value=_format_metric(
                                    snapshot.output_velocity_rad_s,
                                    suffix="rad/s",
                                    fallback=unavailable_value,
                                ),
                                label_size=caption_size,
                                value_size=value_size,
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
        alignment=ft.Alignment.TOP_CENTER,
        padding=ft.Padding(0, card_gap, 0, card_gap),
        content=ft.Container(
            width=content_width,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=card_gap,
                controls=rows,
            ),
        ),
    )
