from dataclasses import dataclass
import flet as ft


@dataclass
class NavItem:
    name: str
    label: str
    icon: ft.IconData
    selected_icon: ft.IconData
