"""
DiscordBot: An Asynchronous Discord Bot for Posting RSS Feed Updates

This bot periodically checks configured RSS feeds and posts new entries
to designated Discord channels. Key features include:
  - Asynchronous RSS feed updates via an RSSReader instance.
  - Concurrent processing of multiple feeds and their entries.
  - Graceful error handling to avoid disruptions in execution.
  - Built-in healthcheck endpoints for liveness and readiness monitoring.
"""

import logging
import asyncio
from typing import List, Optional
from aiohttp import web

import discord
import reader
from reader.types import Entry
from discord.ext import tasks

from discord_rss_bot.rss import RSSReader
from discord_rss_bot.message import format_entry_for_discord
from discord_rss_bot.models import FeedConfig


class DiscordBot(discord.Client):
    """Custom Discord bot class for posting RSS updates."""

    def __init__(self, rss_reader: RSSReader, **kwargs):
        """Initialize the bot."""
        super().__init__(**kwargs)
        self.rss_reader = rss_reader
        self.is_ready_flag = False

    async def on_ready(self):
        """Runs when the bot successfully connects to Discord."""
        logging.info(
            "Logged in as %s (ID: %s)",
            self.user,
            self.user.id,  # pyright: ignore[reportOptionalMemberAccess]
        )
        self.is_ready_flag = True  # Mark bot as ready
        self.check_feeds.start()  # Start the periodic task

    @tasks.loop(minutes=5)
    async def check_feeds(self):
        """Fetches updates for all feeds and processes them."""
        logging.info("Checking for new RSS updates...")
        await self.rss_reader.update_feeds(scheduled=True)

        feeds = [
            self._process_feed(feed) for feed in self.rss_reader.config.feeds
        ]
        await asyncio.gather(*feeds)  # Process all feeds concurrently

    async def _process_feed(self, feed: FeedConfig) -> None:
        """Processes a single RSS feed and posts updates to Discord."""
        try:
            unread_entries = await self.rss_reader.get_unread_entries(
                feed.feed_url
            )

            if not unread_entries:
                logging.info("No unread entries for feed %s", feed.feed_url)
                return

            channel = self._get_channel(feed.channel_id)
            if not channel:
                logging.error(
                    "Invalid channel ID %s for feed %s",
                    feed.channel_id,
                    feed.feed_url,
                )
                return

            await self._process_entries(unread_entries, feed, channel)

            # Mark entries as read after successful processing
            await self.rss_reader.mark_entries_as_read(unread_entries)

        except (reader.ReaderError, discord.DiscordException) as e:
            logging.error("Error processing feed %s: %s", feed.feed_url, e)

    async def _process_entries(
        self,
        entries: List["Entry"],
        feed: FeedConfig,
        channel: discord.TextChannel,
    ) -> None:
        """Sends RSS entries to the designated Discord channel."""
        logging.info(
            "Sending %d entries to channel %s", len(entries), feed.channel_id
        )

        message_tasks = [
            self._send_entry(entry, feed, channel)
            for entry in reversed(entries)
        ]
        await asyncio.gather(*message_tasks)  # Send all messages concurrently

    async def _send_entry(
        self, entry: "Entry", feed: FeedConfig, channel: discord.TextChannel
    ) -> None:
        """Formats and sends an RSS entry to a Discord channel."""
        try:
            message_embded = format_entry_for_discord(entry)
            await channel.send(embed=message_embded)
            logging.info(
                "Sent entry %s to channel %s", entry.link, feed.channel_id
            )

        except discord.DiscordException as e:
            logging.error(
                "Error sending entry %s to channel %s: %s",
                entry.link,
                feed.channel_id,
                e,
            )
            error_message = (
                f"❗ Failed to send entry [{entry.link}] due to an error: {e}"
            )
            await channel.send(error_message)  # Notify in Discord channel

    def _get_channel(
        self, channel_id: int | str
    ) -> Optional[discord.TextChannel]:
        """Retrieves and validates the Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if isinstance(channel, discord.TextChannel):
                return channel

            logging.error(
                "Channel with ID %s is not a TextChannel (got %s).",
                channel_id,
                type(channel).__name__,
            )
            return None

        except (ValueError, TypeError) as e:
            logging.error("Invalid channel ID %s: %s", channel_id, e)
            return None

    async def start_healthchecks(self):
        """Start a lightweight web server for readiness & liveness checks."""
        logging.info("Starting healthcheck server...")
        app = web.Application()
        app.router.add_get("/healthz", self.liveness_probe)
        app.router.add_get("/readyz", self.readiness_probe)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)  # Expose healthcheck API
        await site.start()

    async def liveness_probe(self, _request):
        """Liveness probe – Returns 200 if bot is running."""
        return web.Response(text="I'm alive!", status=200)

    async def readiness_probe(self, _request):
        """Readiness probe – Returns 200 if bot is ready to process requests."""
        if self.is_ready_flag:
            return web.Response(text="I'm ready!", status=200)
        return web.Response(text="I'm not ready yet.", status=503)

    async def start(self, token: str, *_args, **_kwargs):
        """Start the bot and healthcheck server in parallel."""
        await asyncio.gather(
            # Start healthchecks
            self.start_healthchecks(),
            # Start Discord bot
            super().start(token),
        )
