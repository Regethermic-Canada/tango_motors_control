import flet as ft
from flet.controls.control_event import Event
from flet.controls.control_event import ControlEventHandler
from flet.controls.material.icon_button import IconButton

from components.native.icon_button import TangoIconButton
from components.native.nav_item import TangoNavItem
from components.native.text import TangoText
from contexts.locale import LocaleContext
from contexts.route import RouteContext
from models.controls import NavItem
from models.app_model import AppModel
from theme import colors, shadows
from theme.scale import get_viewport_metrics

ContainerHandler = ControlEventHandler[ft.Container] | None


@ft.component
def LanguageSelector() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)
    diameter = int(round((32 if metrics.compact else 40) * metrics.scale))
    label_size = int(round((13 if metrics.compact else 14) * metrics.scale))
    next_locale = "fr" if loc.locale == "en" else "en"

    def on_toggle_language(_: Event[ft.Container]) -> None:
        loc.set_locale(next_locale)

    return ft.Container(
        width=diameter,
        height=diameter,
        alignment=ft.Alignment.CENTER,
        bgcolor=colors.SURFACE,
        border=ft.border.all(1, colors.OUTLINE),
        border_radius=diameter / 2,
        shadow=shadows.soft_shadow(metrics.scale),
        ink=True,
        tooltip=loc.t("select_language"),
        on_click=on_toggle_language,
        content=TangoText(
            next_locale.upper(),
            variant="label",
            size=label_size,
            color=colors.TEXT,
        ),
    )


@ft.component
def Group(item: NavItem, selected: bool) -> ft.Control:
    route_context = ft.use_context(RouteContext)
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)
    icon_size = int(round(22 * metrics.scale))
    return TangoNavItem(
        icon=item.icon,
        selected_icon=item.selected_icon,
        selected=selected,
        tooltip=item.label,
        icon_size=icon_size,
        size=int(round((40 if metrics.compact else 48) * metrics.scale)),
        on_click=lambda _: route_context.navigate(f"/{item.name}"),
    )


@ft.component
def Groups(nav_items: list[NavItem], selected_name: str | None) -> ft.Control:
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)
    nav_width = int(round((40 if metrics.compact else 48) * metrics.scale))
    return ft.Column(
        expand=True,
        spacing=0,
        scroll=ft.ScrollMode.ALWAYS,
        width=nav_width,
        controls=[
            Group(item, selected=(item.name == selected_name)) for item in nav_items
        ],
    )


@ft.component
def AdminModeToggle(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    metrics = get_viewport_metrics(ft.context.page, min_scale=0.7)
    is_admin = app_model.route in ["/admin", "/auth"]

    def on_admin_click(_: Event[IconButton]) -> None:
        if is_admin:
            app_model.navigate("/")
        else:
            app_model.navigate("/auth")

    return TangoIconButton(
        icon=ft.Icons.SETTINGS if not is_admin else ft.Icons.HOME,
        icon_size=int(round(18 * metrics.scale)),
        tooltip=loc.t("admin_settings") if not is_admin else loc.t("main_view"),
        on_click=on_admin_click,
        variant="primary" if is_admin else "surface",
        size="sm" if metrics.compact else "md",
    )
