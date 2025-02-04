from discord_rss_bot.utils import load_config, get_bot_token, get_arguments
from discord_rss_bot.rss_reader import RSSReader
from discord_rss_bot.bot import DiscordBot

import discord

import logging
import argparse
import asyncio
import sys


async def main() -> None:
    """Main asynchronous function for starting the bot."""
    args: argparse.Namespace = get_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("discord").setLevel(log_level)

    bot_token = get_bot_token(args)
    config = load_config(args.config)
    try:
        # Initialize the RSS reader.
        rss_reader = RSSReader(config)
        await rss_reader.setup()

        # Create the Discord client with default intents.
        intents = discord.Intents.default()
        bot = DiscordBot(rss_reader, intents=intents, root_logger=True)
        await bot.start(bot_token)

    except Exception as e:
        logging.error("An unrecoverable error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
