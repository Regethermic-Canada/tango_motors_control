import flet as ft
import random
import threading
import time

class MotorControl(ft.Container):
    def __init__(self, motor_name, initial_speed=0):
        super().__init__()
        self.motor_name = motor_name
        self.speed = initial_speed
        self.is_running = False
        self.load_value = 0.0
        
        # UI components
        self.status_text = ft.Text("STOPPED", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
        self.slider_speed = ft.Slider(
            min=0, max=100, divisions=10, value=self.speed, label="{value}%",
            on_change=self.change_speed, disabled=True
        )
        self.speed_text = ft.Text(f"{self.speed} RPM")
        self.pb_load = ft.ProgressBar(width=150, value=0, color=ft.Colors.BLUE)
        
        # Container properties
        self.padding = 20
        self.bgcolor = ft.Colors.GREY_200
        self.border_radius = 10
        self.width = 300
        
        # Build content
        self.content = self._build_content()

    def did_mount(self):
        # Simulate load changes in background
        self.running_simulation = True
        self.sim_thread = threading.Thread(target=self.simulate_load, daemon=True)
        self.sim_thread.start()

    def will_unmount(self):
        self.running_simulation = False

    def simulate_load(self):
        while self.running_simulation:
            if self.is_running:
                # Fluctuate load based on speed
                base_load = (self.speed / 100) * 0.8
                fluctuation = random.uniform(-0.05, 0.05)
                self.load_value = max(0.0, min(1.0, base_load + fluctuation))
            else:
                self.load_value = 0.0
            
            self.update_load_visuals()
            time.sleep(0.5)

    def update_load_visuals(self):
        try:
            if self.page:
                self.pb_load.value = self.load_value
                # Change color based on load
                if self.load_value > 0.9:
                    self.pb_load.color = ft.Colors.RED
                elif self.load_value > 0.7:
                    self.pb_load.color = ft.Colors.ORANGE
                else:
                    self.pb_load.color = ft.Colors.BLUE
                self.pb_load.update()
        except Exception:
            pass # Handle race conditions during unmount

    def toggle_motor(self, e):
        self.is_running = e.control.value
        self.slider_speed.disabled = not self.is_running
        self.status_text.value = "RUNNING" if self.is_running else "STOPPED"
        self.status_text.color = ft.Colors.GREEN if self.is_running else ft.Colors.RED
        self.update()

    def change_speed(self, e):
        self.speed = e.control.value
        self.speed_text.value = f"{int(self.speed)} RPM"
        self.speed_text.update()

    def _build_content(self):
        return ft.Column([
            ft.Row([
                ft.Icon("settings_input_component", size=30),
                ft.Text(self.motor_name, size=20, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                ft.Switch(label="Power", on_change=self.toggle_motor)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([
                ft.Text("Speed Control:"),
                self.speed_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.slider_speed,
            ft.Row([
                ft.Text("Motor Load:"),
                self.status_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.pb_load,
        ])

def main(page: ft.Page):
    page.title = "Tango Motors Control"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1000
    page.window_height = 800

    # Header with Logo
    header = ft.Container(
        content=ft.Row([
            ft.Image(src="tango_logo.png", height=60, fit="contain"),
            ft.Text("Tango Motors Control", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton("notifications"),
            ft.IconButton("account_circle"),
        ], alignment=ft.MainAxisAlignment.START),
        padding=20,
        bgcolor=ft.Colors.SURFACE,
    )

    # Hero/Banner Section
    banner = ft.Container(
        content=ft.Image(
            src="regethermic_screensaver.png",
            width=1000, 
            height=200,
            fit="cover",
            border_radius=10,
            opacity=0.8
        ),
        padding=20,
        alignment=ft.Alignment.CENTER
    )

    # Dashboard Grid
    motors_grid = ft.Row(
        [
            MotorControl("Conveyor Belt A"),
            MotorControl("Hydraulic Pump B"),
            MotorControl("Cooling Fan C"),
        ],
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    # Main Content Area
    content = ft.Column([
        header,
        banner,
        ft.Container(
            content=ft.Text("System Overview", size=24, weight=ft.FontWeight.BOLD),
            padding=ft.Padding.only(left=20, top=10)
        ),
        ft.Container(motors_grid, padding=20)
    ], scroll=ft.ScrollMode.AUTO)

    page.add(content)

if __name__ == "__main__":
    ft.run(main)
