import flet as ft
from models.app_model import AppModel
from contexts.locale import LocaleContext


@ft.component
def AdminView(app_model: AppModel) -> ft.Control:
    loc = ft.use_context(LocaleContext)

    def on_locale_change(e: ft.ControlEvent) -> None:
        new_locale = e.data
        if isinstance(new_locale, list):
            new_locale = new_locale[0]
        # Flet SegmentedButton returns a string representation of a list or a list of strings
        # Cleanup the value if it's like "['en']"
        new_locale = new_locale.strip("[]'\"")
        app_model.set_locale(new_locale)

    def on_theme_change(e: ft.ControlEvent) -> None:
        app_model.toggle_theme()

    def on_timeout_change(e: ft.ControlEvent) -> None:
        app_model.set_inactivity_timeout(float(e.control.value))

    new_passcode_ref = ft.use_ref(ft.TextField)
    confirm_passcode_ref = ft.use_ref(ft.TextField)
    passcode_error, set_passcode_error = ft.use_state("")
    passcode_success, set_passcode_success = ft.use_state(False)

    def on_change_passcode(e: ft.ControlEvent) -> None:
        p1 = new_passcode_ref.current.value
        p2 = confirm_passcode_ref.current.value
        if not p1 or not p2:
            return
        if p1 == p2:
            app_model.update_admin_passcode(p1)
            set_passcode_error("")
            set_passcode_success(True)
            new_passcode_ref.current.value = ""
            confirm_passcode_ref.current.value = ""
            new_passcode_ref.current.update()
            confirm_passcode_ref.current.update()
        else:
            set_passcode_error(loc.t("passcode_mismatch"))
            set_passcode_success(False)

    return ft.Container(
        expand=True,
        padding=ft.Padding(40, 40, 40, 40),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=30,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            loc.t("admin_settings"),
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: app_model.navigate("/"),
                        ),
                    ],
                ),
                ft.Divider(),
                
                # Locale Section
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(loc.t("locale"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                        ft.SegmentedButton(
                            selected={app_model.locale},
                            on_change=on_locale_change,
                            segments=[
                                ft.Segment(
                                    value="en",
                                    label=ft.Text(loc.t("en")),
                                    icon=ft.Icon(ft.Icons.LANGUAGE),
                                ),
                                ft.Segment(
                                    value="fr",
                                    label=ft.Text(loc.t("fr")),
                                    icon=ft.Icon(ft.Icons.LANGUAGE),
                                ),
                            ],
                        ),
                    ],
                ),

                # Theme Section
                ft.ListTile(
                    title=ft.Text(loc.t("theme_mode")),
                    subtitle=ft.Text(loc.t(f"{app_model.theme_mode.value}_mode")),
                    leading=ft.Icon(ft.Icons.BRIGHTNESS_4),
                    trailing=ft.Switch(
                        value=app_model.theme_mode == ft.ThemeMode.DARK,
                        on_change=on_theme_change,
                    ),
                ),

                # Inactivity Timeout Section
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(loc.t("inactivity_timeout"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                                ft.Text(f"{int(app_model.inactivity_limit)} {loc.t('seconds')}"),
                            ]
                        ),
                        ft.Slider(
                            min=10,
                            max=300,
                            divisions=29,
                            label="{value}s",
                            value=app_model.inactivity_limit,
                            on_change=on_timeout_change,
                        ),
                    ],
                ),

                ft.Divider(),

                # Change Passcode Section
                ft.Column(
                    spacing=15,
                    controls=[
                        ft.Text(loc.t("change_passcode"), theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                        ft.TextField(
                            ref=new_passcode_ref,
                            label=loc.t("new_passcode"),
                            password=True,
                            can_reveal_password=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=300,
                        ),
                        ft.TextField(
                            ref=confirm_passcode_ref,
                            label=loc.t("confirm_passcode"),
                            password=True,
                            can_reveal_password=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            width=300,
                        ),
                        ft.Text(
                            passcode_error,
                            color=ft.Colors.ERROR,
                            visible=bool(passcode_error),
                        ),
                        ft.Text(
                            loc.t("passcode_updated"),
                            color=ft.Colors.GREEN,
                            visible=passcode_success,
                        ),
                        ft.ElevatedButton(
                            loc.t("save"),
                            icon=ft.Icons.SAVE,
                            on_click=on_change_passcode,
                        ),
                    ],
                ),

                ft.Divider(),
                
                ft.ElevatedButton(
                    loc.t("back_to_main"),
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: app_model.navigate("/"),
                    width=200,
                    height=50,
                ),
            ],
        ),
    )
