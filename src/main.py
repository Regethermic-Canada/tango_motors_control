import flet as ft

from components.app import App
from utils.config import config
from utils.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging(level=config.log_level)
    ft.run(  # pyright: ignore[reportUnknownMemberType]
        lambda page: page.render_views(
            lambda: App()
        ),  # pyright: ignore[reportUnknownMemberType]
        assets_dir="assets",
    )
