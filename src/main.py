import flet as ft
import time
import threading
from typing import Optional

class TangoCounterApp:
    INACTIVITY_LIMIT: float = 30.0
    ASSET_LOGO: str = "tango_logo.png"
    ASSET_SCREENSAVER: str = "regethermic_screensaver.png"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        
        # State
        self._counter_val: int = 0
        self._last_interaction: float = time.time()
        self._is_screensaver_active: bool = False
        self._running: bool = True
        
        # Controls
        self.counter_display = ft.Text(
            value="0", 
            size=80, 
            weight=ft.FontWeight.BOLD
        )
        self.theme_icon = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            on_click=self.toggle_theme,
            tooltip="Toggle Theme"
        )
        self.screensaver_overlay = self._build_screensaver()
        
        # Initialization
        self.build_ui()
        self.start_inactivity_monitor()

    def setup_page(self):
        self.page.title = "Tango Motors Control"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        
        # Global Event Listeners
        self.page.on_pointer_down = self.reset_timer
        self.page.on_keyboard_event = self.reset_timer

    # Logic

    def reset_timer(self, e: Optional[ft.ControlEvent] = None):
        """Resets the inactivity timer and dismisses screensaver if active."""
        self._last_interaction = time.time()
        if self._is_screensaver_active:
            self.dismiss_screensaver()

    def dismiss_screensaver(self):
        self._is_screensaver_active = False
        self.screensaver_overlay.visible = False
        self.screensaver_overlay.update()

    def activate_screensaver(self):
        if not self._is_screensaver_active:
            self._is_screensaver_active = True
            self.screensaver_overlay.visible = True
            self.screensaver_overlay.update()

    def increment(self, e: ft.ControlEvent):
        self._counter_val += 1
        self.update_counter()
        self.reset_timer()

    def decrement(self, e: ft.ControlEvent):
        self._counter_val -= 1
        self.update_counter()
        self.reset_timer()

    def update_counter(self):
        self.counter_display.value = str(self._counter_val)
        self.counter_display.update()

    def toggle_theme(self, e: ft.ControlEvent):
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.LIGHT if is_dark else ft.ThemeMode.DARK
        self.theme_icon.icon = ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE
        self.page.update()
        self.reset_timer()

    # UI

    def _build_screensaver(self) -> ft.Container:
        return ft.Container(
            visible=False,
            expand=True,
            bgcolor=ft.Colors.BLACK,
            alignment=ft.Alignment.CENTER,
            on_click=self.reset_timer,
            content=ft.Image(
                src=self.ASSET_SCREENSAVER,
                fit="cover",
                opacity=0.8
            )
        )

    def build_ui(self):
        # 1. Background Layer (Bottom)
        background = ft.Container(
            expand=True,
            alignment=ft.Alignment.BOTTOM_CENTER,
            padding=ft.Padding(0, 0, 0, 60),
            opacity=0.1,
            content=ft.Image(src=self.ASSET_LOGO, width=400, fit="contain")
        )

        # 2. Controls Layer
        controls_layer = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
                controls=[
                    self.counter_display,
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REMOVE, 
                                icon_size=40, 
                                on_click=self.decrement
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD, 
                                icon_size=40, 
                                on_click=self.increment
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=40
                    )
                ]
            )
        )

        # 3. Header Layer
        header_layer = ft.Container(
            content=self.theme_icon,
            top=20,
            right=20,
        )

        # Stack Composition
        self.page.add(
            ft.Stack(
                expand=True,
                controls=[
                    background,
                    controls_layer,
                    header_layer,
                    self.screensaver_overlay
                ]
            )
        )

    # Background Tasks

    def start_inactivity_monitor(self):
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()

    def _monitor_loop(self):
        while self._running:
            time.sleep(1.0)
            elapsed = time.time() - self._last_interaction
            if elapsed > self.INACTIVITY_LIMIT:
                self.activate_screensaver()

def main(page: ft.Page):
    TangoCounterApp(page)

if __name__ == "__main__":
    ft.run(main)
