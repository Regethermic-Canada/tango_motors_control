import flet as ft
from components.app import App
from utils.logging_config import setup_logging
from utils.config import config


def main(page: ft.Page) -> None:
    page.title = config.app_title

    # Render the App component
    # Lambda that returns the component for page.render_views
    page.render_views(lambda: [App()])  # pyright: ignore[reportUnknownMemberType]


if __name__ == "__main__":
    setup_logging(level=config.log_level)
    ft.run(main, assets_dir="assets")  # pyright: ignore[reportUnknownMemberType]
