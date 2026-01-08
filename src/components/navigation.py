import flet as ft

from contexts.locale import LocaleContext
from contexts.route import RouteContext
from contexts.theme import ThemeContext
from models.controls import NavItem


@ft.component
def LanguageSelector() -> ft.Control:
    loc = ft.use_context(LocaleContext)
    return ft.PopupMenuButton(
        icon=ft.Icons.LANGUAGE,
        tooltip=loc.t("select_language"),
        items=[
            ft.PopupMenuItem(
                content=ft.Text(loc.t("english")),
                on_click=lambda _: loc.set_locale("en"),
                checked=(loc.locale == "en"),
            ),
            ft.PopupMenuItem(
                content=ft.Text(loc.t("french")),
                on_click=lambda _: loc.set_locale("fr"),
                checked=(loc.locale == "fr"),
            ),
        ],
    )


@ft.component
def Group(item: NavItem, selected: bool) -> ft.Control:
    route_context = ft.use_context(RouteContext)
    return ft.Container(
        ink=True,
        padding=10,
        border_radius=5,
        tooltip=item.label,
        bgcolor=ft.Colors.SECONDARY_CONTAINER if selected else ft.Colors.TRANSPARENT,
        content=ft.Row(
            [
                ft.Icon(item.selected_icon if selected else item.icon),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=lambda _: route_context.navigate(f"/{item.name}"),
    )


@ft.component
def Groups(nav_items: list[NavItem], selected_name: str | None) -> ft.Control:
    return ft.Column(
        expand=True,
        spacing=0,
        scroll=ft.ScrollMode.ALWAYS,
        width=60,  # Reduced width for icon-only navigation
        controls=[
            Group(item, selected=(item.name == selected_name)) for item in nav_items
        ],
    )


@ft.component
def PopupColorItem(color: ft.Colors, name_key: str) -> ft.PopupMenuItem:
    theme = ft.use_context(ThemeContext)
    loc = ft.use_context(LocaleContext)
    # Restore dynamic "(default)" label based on current seed color
    is_current = color == theme.seed_color
    name = loc.t(name_key)
    display_name = f"{name} ({loc.t('default_label')})" if is_current else name

    return ft.PopupMenuItem(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=color),
                ft.Text(display_name),
            ],
        ),
        on_click=lambda _: theme.set_seed_color(color),
    )


@ft.component
def ThemeModeToggle() -> ft.Control:
    theme = ft.use_context(ThemeContext)
    loc = ft.use_context(LocaleContext)
    
    tooltip_key = "light_mode" if theme.mode == ft.ThemeMode.DARK else "dark_mode"
    
    return ft.IconButton(
        icon=ft.Icons.DARK_MODE
        if theme.mode == ft.ThemeMode.DARK
        else ft.Icons.LIGHT_MODE,
        tooltip=loc.t(tooltip_key),
        on_click=lambda _: theme.toggle_mode(),
    )


@ft.component
def ThemeSeedColor() -> ft.Control:
    theme = ft.use_context(ThemeContext)
    loc = ft.use_context(LocaleContext)

    color_name = "Unknown"
    # Find the key for the current color
    color_keys = {
        ft.Colors.DEEP_PURPLE: "purple",
        ft.Colors.INDIGO: "indigo",
        ft.Colors.BLUE: "blue",
        ft.Colors.TEAL: "teal",
        ft.Colors.GREEN: "green",
        ft.Colors.YELLOW: "yellow",
        ft.Colors.ORANGE: "orange",
        ft.Colors.DEEP_ORANGE: "deep_orange",
        ft.Colors.PINK: "pink",
    }
    
    current_key = color_keys.get(theme.seed_color, "blue")
    color_name = loc.t(current_key)

    return ft.PopupMenuButton(
        icon=ft.Icons.COLOR_LENS_OUTLINED,
        tooltip=f"{loc.t('theme_color')}: {color_name}",
        items=[
            PopupColorItem(color=ft.Colors.DEEP_PURPLE, name_key="purple"),
            PopupColorItem(color=ft.Colors.INDIGO, name_key="indigo"),
            PopupColorItem(color=ft.Colors.BLUE, name_key="blue"),
            PopupColorItem(color=ft.Colors.TEAL, name_key="teal"),
            PopupColorItem(color=ft.Colors.GREEN, name_key="green"),
            PopupColorItem(color=ft.Colors.YELLOW, name_key="yellow"),
            PopupColorItem(color=ft.Colors.ORANGE, name_key="orange"),
            PopupColorItem(color=ft.Colors.DEEP_ORANGE, name_key="deep_orange"),
            PopupColorItem(color=ft.Colors.PINK, name_key="pink"),
        ],
    )
