import discord
from discord.ext import tasks
import logging
from typing import Optional

from discord_rss_bot.rss_reader import RSSReader
from discord_rss_bot.message import format_entry_for_discord
from discord_rss_bot.models import FeedConfig


class DiscordBot(discord.Client):
    def __init__(self, reader: RSSReader, **kwargs):
        super().__init__(**kwargs)
        self.rss_reader = reader

    async def on_ready(self):
        logging.info(
            f"Logged in as {self.user} (ID: {self.user.id})"  # pyright: ignore[reportOptionalMemberAccess]
        )
        # Start the background task that periodically checks for new feed entries.
        self.check_feeds.start()

    @tasks.loop(minutes=5)
    async def check_feeds(self):
        """Iterates through each feed defined in the config and processes it."""
        await self.rss_reader.update_feeds(scheduled=True)
        for feed in self.rss_reader.config.feeds:
            await self._process_feed(feed)

    async def _process_feed(self, feed: FeedConfig) -> None:
        """Processes a single feed and its designated channel."""
        # Retrieve unread entries for the feed.
        unread_entries = await self.rss_reader.get_unread_entries(feed.feed_url)
        if not unread_entries:
            logging.info(f"No unread entries for feed {feed.feed_url}")
            return

        # Retrieve the Discord channel ensuring it's a TextChannel.
        channel = self._get_channel(feed.channel_id)
        if channel is None:
            logging.error(
                f"Channel with ID {feed.channel_id} not found or invalid for feed {feed.feed_url}."
            )
            return

        # Process and send each entry.
        await self._process_entries(unread_entries, feed, channel)
        # Mark all processed entries as read.
        await self.rss_reader.mark_entries_as_read(unread_entries)

    async def _process_entries(
        self, entries, feed: FeedConfig, channel: discord.TextChannel
    ) -> None:
        """Iterates over each entry and sends it to the specified Discord channel."""
        for entry in entries:
            await self._send_entry(entry, feed, channel)

    async def _send_entry(
        self, entry, feed: FeedConfig, channel: discord.TextChannel
    ) -> None:
        """Formats a single entry and sends it to the given Discord channel."""
        message = format_entry_for_discord(entry)
        logging.info(f"Sending entry {entry.link} to channel {feed.channel_id}")
        try:
            await channel.send(embed=message)
        except Exception as e:
            logging.error(
                f"Error sending entry {entry.link} to channel {feed.channel_id}: {e}"
            )

    def _get_channel(self, channel_id) -> Optional[discord.TextChannel]:
        """
        Retrieves the Discord channel corresponding to channel_id.
        Returns the channel only if it is a TextChannel; otherwise,
        returns None.
        """
        try:
            channel = self.get_channel(int(channel_id))
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid channel_id '{channel_id}': {e}")
            return None

        if isinstance(channel, discord.TextChannel):
            return channel
        else:
            logging.error(
                f"Channel with ID {channel_id} is not a TextChannel (got {type(channel).__name__})."
            )
            return None
