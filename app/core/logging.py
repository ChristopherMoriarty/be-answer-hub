import logging
import sys


def init_logger(level: str) -> None:
    """Initialize application logger with stdout output."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
