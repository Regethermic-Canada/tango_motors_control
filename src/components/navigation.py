import flet as ft

from contexts.route import RouteContext
from contexts.theme import ThemeContext
from models.controls import NavItem


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
def PopupColorItem(color: ft.Colors, name: str) -> ft.PopupMenuItem:
    theme = ft.use_context(ThemeContext)
    return ft.PopupMenuItem(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=color),
                ft.Text(name),
            ],
        ),
        on_click=lambda _: theme.set_seed_color(color),
    )


@ft.component
def ThemeModeToggle() -> ft.Control:
    theme = ft.use_context(ThemeContext)
    return ft.IconButton(
        icon=(
            ft.Icons.DARK_MODE
            if theme.mode == ft.ThemeMode.DARK
            else ft.Icons.LIGHT_MODE
        ),
        tooltip=f"Switch to {'Light' if theme.mode == ft.ThemeMode.DARK else 'Dark'} mode",
        on_click=lambda _: theme.toggle_mode(),
    )


@ft.component
def ThemeSeedColor() -> ft.Control:
    theme = ft.use_context(ThemeContext)

    # Helper to get a readable name for the seed color
    color_name = "Unknown"
    color_name = theme.seed_color.replace("_", " ").title()

    return ft.PopupMenuButton(
        icon=ft.Icons.COLOR_LENS_OUTLINED,
        tooltip=f"Theme color: {color_name}",
        items=[
            PopupColorItem(color=ft.Colors.DEEP_PURPLE, name="Deep purple"),
            PopupColorItem(color=ft.Colors.INDIGO, name="Indigo"),
            PopupColorItem(color=ft.Colors.BLUE, name="Blue (default)"),
            PopupColorItem(color=ft.Colors.TEAL, name="Teal"),
            PopupColorItem(color=ft.Colors.GREEN, name="Green"),
            PopupColorItem(color=ft.Colors.YELLOW, name="Yellow"),
            PopupColorItem(color=ft.Colors.ORANGE, name="Orange"),
            PopupColorItem(color=ft.Colors.DEEP_ORANGE, name="Deep orange"),
            PopupColorItem(color=ft.Colors.PINK, name="Pink"),
        ],
    )
