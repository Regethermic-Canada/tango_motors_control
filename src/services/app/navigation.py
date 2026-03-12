import logging

import flet as ft

logger = logging.getLogger(__name__)


@ft.observable
class NavigationService:
    def __init__(self, route: str = "/") -> None:
        self.route = route

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        logger.info("Route changed from: %s to: %s", self.route, e.route)
        self.route = e.route

    def navigate(self, new_route: str) -> None:
        if new_route == self.route:
            return

        logger.info("Navigating to: %s", new_route)
        ft.context.page.go(new_route)

    async def view_popped(self, e: ft.ViewPopEvent) -> None:
        logger.info("View popped")
        views = ft.unwrap_component(ft.context.page.views)
        if len(views) > 1:
            ft.context.page.go(views[-2].route)
