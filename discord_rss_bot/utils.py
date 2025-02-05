"""
Utility functions for the bot application.

This module provides:
- Configuration loading and validation.
- Argument parsing for command-line execution.
- Environment variable handling for the bot token.
"""

import argparse
import os
import logging
import sys

import yaml
from pydantic import ValidationError
from discord_rss_bot.models import ConfigFile


def get_bot_token(args: argparse.Namespace) -> str:
    """Get the bot token from arguments or environment"""
    logging.info("Loading bot token")
    token_sources = [
        args.token,
        os.getenv("DISCORD_BOT_TOKEN"),
    ]
    for token in token_sources:
        if token:
            logging.debug("Found bot token: %s", token)
            return token
    raise ValueError("Bot token was not provided.")


def load_config(config_path: str) -> ConfigFile:
    """Load the config file."""
    logging.info("Loading configuration from %s", config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            return ConfigFile(**config_data)

    except FileNotFoundError:
        logging.error("Configuration file not found at: %s", config_path)
    except ValidationError as e:
        logging.error("Configuration validation failed: %s", e)
    except yaml.YAMLError as e:
        logging.error("YAML parsing error in config file: %s", e)

    sys.exit(1)


def get_arguments() -> argparse.Namespace:
    """Parses and returns command line arguments."""
    parser = argparse.ArgumentParser(
        description="Discord RSS Bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-t",
        "--token",
        action="store",
        help="Bot token (overrides env. variable).",
        required=False,
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        help="Path to config file.",
        required=False,
        default="config.yaml",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Should we run the bot in debug mode?",
        required=False,
    )
    return parser.parse_args()
