import flet as ft

from contexts.locale import LocaleContext


@ft.component
def LoadingSpinner(size: int = 56) -> ft.Control:
    loc = ft.use_context(LocaleContext)
    return ft.Container(
        key="app-loading",
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.ProgressRing(
            width=size,
            height=size,
            semantics_label=loc.t("loading_interface", "Loading"),
        ),
    )
