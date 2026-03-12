"""Main entry point for the AIHawk Job Application Bot."""

import traceback
from pathlib import Path

from src.app_config import AppConfig, ConfigError
from src.cli import handle_inquiries, prompt_user_action
from src.logging import logger


def main():
    """Main entry point for the AIHawk Job Application Bot."""
    try:
        # Load and validate all configuration from the data folder
        app_config = AppConfig.from_data_folder(Path("data_folder"))

        # Interactive prompt for user to select actions
        selected_actions = prompt_user_action()

        # Handle selected actions and execute them
        handle_inquiries(selected_actions, app_config)

    except ConfigError as ce:
        logger.error(f"Configuration error: {ce}")
        logger.error(
            "Check that data_folder/work_preferences.yaml and data_folder/secrets.yaml "
            "exist and contain all required fields. "
            "See data_folder_example/ for reference templates."
        )
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {fnf}")
        logger.error("Ensure all required files are present in the data folder.")
    except RuntimeError as re:
        logger.error(f"Runtime error: {re}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
