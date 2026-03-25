from collections.abc import Callable
import flet as ft
from flet.controls.control_event import Event
from flet.controls.material.button import Button
from typing import Literal
from components.views.admin.admin_passcode_sheet import AdminPasscodeSheet
from components.views.main.motor_status_sheet import MotorStatusSheet
from components.ui.card import TangoCard
from components.ui.page import TangoPage
from components.ui.sheet import TangoSheet
from components.ui.slider import TangoSlider
from components.ui.text import TangoText
from components.ui.tango_toast import ToastType, show_toast
from components.ui.button import TangoButton
from contexts.motor import MotorContext
from contexts.settings import SettingsContext
from contexts.locale import LocaleContext
from theme import colors, spacing
from theme.scale import ViewportArea, get_viewport_metrics, resolve_panel_width


@ft.component
def AdminView() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    motor = ft.use_context(MotorContext).current()
    settings_service = ft.use_context(SettingsContext).current()
    active_sheet, set_active_sheet = ft.use_state("")
    inactivity_timeout_draft, set_inactivity_timeout_draft = ft.use_state(
        float(settings_service.inactivity_timeout)
    )
    default_speed_draft, set_default_speed_draft = ft.use_state(
        float(settings_service.default_speed)
    )
    new_passcode, set_new_passcode = ft.use_state("")
    confirm_passcode, set_confirm_passcode = ft.use_state("")
    is_passcode_saving, set_is_passcode_saving = ft.use_state(False)
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
    action_button_size = int(round((18 if metrics.is_compact else 19) * metrics.scale))
    action_button_variant_size: Literal["md", "lg"] = (
        "md" if metrics.is_compact else "lg"
    )
    action_button_spacing = int(
        round((spacing.XS if metrics.is_compact else spacing.MD) * metrics.scale)
    )
    motor_status_snapshots = motor.get_status_snapshots()

    def sync_slider_drafts() -> None:
        set_inactivity_timeout_draft(float(settings_service.inactivity_timeout))
        set_default_speed_draft(float(settings_service.default_speed))

    ft.use_effect(
        sync_slider_drafts,
        [
            settings_service.inactivity_timeout,
            settings_service.default_speed,
        ],
    )

    def show_settings_toast(message_key: str) -> None:
        show_toast(
            page=ft.context.page,
            type=ToastType.INFO,
            build=lambda: settings_service.t(message_key),
        )

    def on_timeout_commit(value: float) -> None:
        committed_value = float(round(value))
        set_inactivity_timeout_draft(committed_value)
        if settings_service.inactivity_timeout == committed_value:
            return
        settings_service.set_inactivity_timeout(committed_value)
        show_settings_toast("inactivity_timeout_updated")

    def on_default_speed_commit(value: float) -> None:
        committed_value = int(round(value))
        set_default_speed_draft(float(committed_value))
        if settings_service.default_speed == committed_value:
            return
        settings_service.set_default_speed(committed_value)
        show_settings_toast("default_speed_updated")

    timeout_label = TangoText(
        loc.t("inactivity_timeout"),
        variant="subtitle",
        size=section_title_size,
    )
    timeout_value = TangoText(
        f"{int(round(inactivity_timeout_draft))} {loc.t('seconds')}",
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
        str(int(round(default_speed_draft))),
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

    def reset_passcode_sheet_state() -> None:
        set_new_passcode("")
        set_confirm_passcode("")
        set_is_passcode_saving(False)

    def close_passcode_sheet() -> None:
        reset_passcode_sheet_state()
        set_active_sheet("")

    def close_motor_status_sheet() -> None:
        set_active_sheet("")

    passcode_sheet_content = (
        AdminPasscodeSheet(
            new_passcode=new_passcode,
            set_new_passcode=set_new_passcode,
            confirm_passcode=confirm_passcode,
            set_confirm_passcode=set_confirm_passcode,
            is_saving=is_passcode_saving,
            set_is_saving=set_is_passcode_saving,
            on_close=close_passcode_sheet,
        )
        if active_sheet == "passcode"
        else None
    )

    def on_change_admin_passcode_click(_: Event[Button]) -> None:
        reset_passcode_sheet_state()
        set_active_sheet("passcode")

    def on_motor_status_click(_: Event[Button]) -> None:
        set_active_sheet("motor_status")

    active_sheet_title: str | None = None
    active_sheet_content: ft.Control | None = None
    active_sheet_scrollable = False
    active_sheet_on_dismiss: Callable[[], None] | None = None

    if active_sheet == "passcode":
        active_sheet_title = loc.t("change_admin_passcode")
        active_sheet_content = passcode_sheet_content
        active_sheet_scrollable = False
        active_sheet_on_dismiss = close_passcode_sheet
    elif active_sheet == "motor_status":
        active_sheet_title = loc.t("motor_status_sheet_title")
        active_sheet_content = MotorStatusSheet(statuses=motor_status_snapshots)
        active_sheet_scrollable = True
        active_sheet_on_dismiss = close_motor_status_sheet

    sheet_action_buttons: ft.Control = ft.Row(
        spacing=action_button_spacing,
        controls=[
            ft.Container(
                expand=True,
                content=TangoButton(
                    text=loc.t("change_admin_passcode"),
                    variant="secondary",
                    expand=True,
                    size=action_button_variant_size,
                    text_size=action_button_size,
                    on_click=on_change_admin_passcode_click,
                ),
            ),
            ft.Container(
                expand=True,
                content=TangoButton(
                    text=loc.t("motor_status_sheet_title"),
                    variant="secondary",
                    expand=True,
                    size=action_button_variant_size,
                    text_size=action_button_size,
                    icon=ft.Icons.TUNE,
                    on_click=on_motor_status_click,
                ),
            ),
        ],
    )

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
                    content=ft.Container(
                        width=card_width,
                        expand=True,
                        content=TangoCard(
                            expand=True,
                            scrollable=True,
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
                                    TangoSlider(
                                        min=10,
                                        max=150,
                                        divisions=14,
                                        label="{value}s",
                                        value=inactivity_timeout_draft,
                                        set_value=set_inactivity_timeout_draft,
                                        on_commit=on_timeout_commit,
                                        scale=slider_scale,
                                    ),
                                    ft.Divider(height=section_spacing),
                                    default_speed_header,
                                    TangoSlider(
                                        min=settings_service.default_speed_min,
                                        max=settings_service.default_speed_max,
                                        divisions=settings_service.default_speed_max
                                        * 2,
                                        label="{value}",
                                        value=default_speed_draft,
                                        set_value=set_default_speed_draft,
                                        on_commit=on_default_speed_commit,
                                        scale=slider_scale,
                                    ),
                                    ft.Divider(height=section_spacing),
                                    admin_passcode_label,
                                    admin_passcode_description,
                                    sheet_action_buttons,
                                ],
                            ),
                        ),
                    ),
                ),
                TangoSheet(
                    open=active_sheet != "",
                    title=active_sheet_title,
                    content=active_sheet_content,
                    scrollable=active_sheet_scrollable,
                    on_dismiss=active_sheet_on_dismiss,
                ),
            ],
        ),
    )
