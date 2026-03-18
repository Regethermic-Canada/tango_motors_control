import asyncio

import flet as ft

from components.shell.activity_boundary import ActivityBoundary
from components.shell.app_body import AppBody
from components.shell.layout import Layout
from components.shell.loading_spinner import LoadingSpinner
from contexts.locale import LocaleContext, LocaleContextValue
from contexts.motor import MotorContext, MotorContextValue
from contexts.route import RouteContext, RouteContextValue
from contexts.settings import SettingsContext, SettingsContextValue
from contexts.shell import ShellContext, ShellContextValue
from services.app.i18n import I18nService
from services.app.navigation import NavigationService
from services.app.runtime import AppRuntime
from services.app.settings import SettingsService
from services.app.shell import ShellService
from services.motors.controller import MotorController
from theme import animation


@ft.component
def App() -> ft.Control:
    navigation, _ = ft.use_state(NavigationService(route=ft.context.page.route))
    i18n_service = ft.use_memo(lambda: I18nService(), dependencies=[])
    settings_service, _ = ft.use_state(SettingsService(i18n_service))
    motor_controller, _ = ft.use_state(MotorController())
    shell_service, _ = ft.use_state(ShellService())
    viewport_size, set_viewport_size = ft.use_state((0.0, 0.0))
    ui_ready, set_ui_ready = ft.use_state(False)
    entry_animation_started, set_entry_animation_started = ft.use_state(False)
    entry_animation_done, set_entry_animation_done = ft.use_state(False)

    _ = settings_service.locale_version
    _ = navigation.route
    _ = viewport_size

    runtime = ft.use_memo(
        lambda: AppRuntime(
            page=ft.context.page,
            motor_controller=motor_controller,
            settings_service=settings_service,
            shell_service=shell_service,
            set_viewport_size=set_viewport_size,
            set_ui_ready=set_ui_ready,
        ),
        dependencies=[
            motor_controller,
            settings_service,
            shell_service,
            set_viewport_size,
            set_ui_ready,
        ],
    )

    ft.context.page.on_route_change = navigation.route_change
    ft.context.page.on_view_pop = navigation.view_popped

    navigate_callback = ft.use_callback(
        lambda new_route: navigation.navigate(new_route),
        dependencies=[navigation.route],
    )
    route_value = ft.use_memo(
        lambda: RouteContextValue(
            route=navigation.route,
            navigate=navigate_callback,
        ),
        dependencies=[navigation.route, navigate_callback],
    )

    set_locale = ft.use_callback(
        lambda loc: settings_service.set_locale(loc),
        dependencies=[settings_service.locale_version],
    )
    locale_value = ft.use_memo(
        lambda: LocaleContextValue(
            locale=settings_service.locale,
            translations=settings_service.translations,
            set_locale=set_locale,
        ),
        dependencies=[settings_service.locale_version, set_locale],
    )
    settings_value = ft.use_memo(
        lambda: SettingsContextValue(service=settings_service),
        dependencies=[settings_service],
    )
    motor_value = ft.use_memo(
        lambda: MotorContextValue(controller=motor_controller),
        dependencies=[motor_controller],
    )
    shell_value = ft.use_memo(
        lambda: ShellContextValue(service=shell_service),
        dependencies=[shell_service],
    )

    def build_loading_shell() -> ft.Container:
        return ft.Container(
            key="app-loading-shell",
            expand=True,
            content=LoadingSpinner(size=80),
        )

    def build_app_shell(*, key: str | None = None) -> ft.Container:
        return ft.Container(
            key=key,
            expand=True,
            content=ActivityBoundary(
                on_activity=shell_service.reset_timer,
                content=Layout(AppBody()),
            ),
        )

    async def complete_entry_animation_task() -> None:
        await asyncio.sleep(animation.APP_SWITCHER_DURATION_MS / 1000)
        set_entry_animation_done(True)

    ft.on_mounted(runtime.on_mounted)
    ft.on_unmounted(runtime.on_unmounted)

    def on_ui_ready_changed() -> None:
        if ui_ready and not entry_animation_started and not entry_animation_done:
            set_entry_animation_started(True)
            ft.context.page.run_task(complete_entry_animation_task)

    ft.on_updated(on_ui_ready_changed, [ui_ready])

    return LocaleContext(
        locale_value,
        lambda: RouteContext(
            route_value,
            lambda: SettingsContext(
                settings_value,
                lambda: MotorContext(
                    motor_value,
                    lambda: ShellContext(
                        shell_value,
                        lambda: ft.View(
                            route="/",
                            padding=0,
                            controls=[
                                (
                                    build_app_shell()
                                    if entry_animation_done
                                    else ft.AnimatedSwitcher(
                                        expand=True,
                                        transition=ft.AnimatedSwitcherTransition.FADE,
                                        duration=animation.APP_SWITCHER_DURATION_MS,
                                        reverse_duration=animation.APP_SWITCHER_REVERSE_DURATION_MS,
                                        content=(
                                            build_app_shell(key="app-ready")
                                            if ui_ready
                                            else build_loading_shell()
                                        ),
                                    )
                                )
                            ],
                        ),
                    ),
                ),
            ),
        ),
    )
