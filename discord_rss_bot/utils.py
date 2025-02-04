import argparse
import os
import logging
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
            logging.debug(f"Found bot token: {token}")
            return token
    raise ValueError("Bot token was not provided.")


def load_config(config_path: str) -> ConfigFile:
    """Load the config file."""
    logging.info(f"Loading config file {config_path}")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            return ConfigFile(**config)
    except FileNotFoundError:
        logging.error("Configuration file not found.")
        exit(1)
    except ValidationError as e:
        logging.error(f"Error validating config.yaml: {e}")
        exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config.yaml: {e}")
        exit(1)


def get_arguments() -> argparse.Namespace:
    """Parses and returns command line arguments."""
    parser = argparse.ArgumentParser()
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
