import logging
import sys
from typing import TextIO


def setup_logging(level: str = "INFO") -> None:
    """
    Configures the logging for the application.
    """
    numeric_level: int = getattr(logging, level.upper(), logging.INFO)

    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    console_handler: logging.StreamHandler[TextIO] = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    logging.info(f"Logging configured successfully with level: {level}")
