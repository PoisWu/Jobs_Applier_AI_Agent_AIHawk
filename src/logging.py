import logging
import logging.handlers
import os
import sys

from loguru import logger
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

from config import settings


def remove_default_loggers() -> None:
    """Remove default loggers from root logger."""
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()


def init_loguru_logger() -> None:
    """Initialize and configure loguru logger."""

    log_file = "log/app.log"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger.remove()

    # Add file logger if LOG_TO_FILE is True
    if settings.LOG_TO_FILE:
        logger.add(
            log_file,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            backtrace=True,
            diagnose=True,
        )

    # Add console logger if LOG_TO_CONSOLE is True
    if settings.LOG_TO_CONSOLE:
        logger.add(
            sys.stderr,
            level=settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            backtrace=True,
            diagnose=True,
        )


def init_selenium_logger() -> None:
    """Initialize and configure selenium logger to write to selenium.log."""
    log_file = "log/selenium.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    selenium_logger.handlers.clear()

    selenium_logger.setLevel(settings.LOG_SELENIUM_LEVEL)

    # Create file handler for selenium logger
    file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=5)
    file_handler.setLevel(settings.LOG_SELENIUM_LEVEL)

    # Define a simplified format for selenium logger entries
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add the file handler to selenium_logger
    selenium_logger.addHandler(file_handler)


remove_default_loggers()
init_loguru_logger()
init_selenium_logger()
