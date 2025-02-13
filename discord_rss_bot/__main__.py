"""
Main entry point for the bot application.

This script initializes the bot by:
- Parsing command-line arguments.
- Configuring logging levels.
- Loading the configuration file.
- Setting up the RSS reader.
- Starting the Discord bot.
"""

import logging
import argparse
import asyncio
import sys

import discord

from discord_rss_bot.utils import load_config, get_bot_token, get_arguments
from discord_rss_bot.rss import RSSReader
from discord_rss_bot.bot import DiscordBot


async def initialize_bot(args: argparse.Namespace) -> None:
    """Initializes and starts the Discord bot with RSS integration."""
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("discord").setLevel(log_level)

    try:
        # Load bot token and configuration
        bot_token = get_bot_token(args)
        config = load_config(args.config)

        # Initialize RSS reader
        rss_reader = RSSReader(config)
        await rss_reader.setup()

        # Initialize Discord bot with default intents
        intents = discord.Intents.default()
        bot = DiscordBot(rss_reader, intents=intents, root_logger=True)

        logging.info("Bot is starting...")
        await bot.start(bot_token)

    # pylint: disable=W0718
    except Exception as e:
        logging.critical(
            "An unrecoverable error occurred: %s", e, exc_info=True
        )
        sys.exit(1)


def main():
    """Main function to start the bot asynchronously."""
    try:
        asyncio.run(initialize_bot(get_arguments()))
    except KeyboardInterrupt:
        logging.info("Bot shutting down gracefully.")
    # pylint: disable=W0718
    except Exception as e:
        logging.critical(
            "Unexpected error in bot execution: %s", e, exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
