""" 
RSSReader class: Asynchronous wrapper around the `reader` library.

This class handles:
- Managing RSS feeds (adding, updating, and removing).
- Retrieving unread entries from feeds.
- Marking entries as read after processing.
- Ensuring efficient asynchronous execution using `asyncio.to_thread()`.

It acts as the data layer for the Discord bot, allowing it to fetch 
and process RSS updates efficiently.
"""

import asyncio
import logging

from typing import List, Optional, Set

from reader import make_reader, ReaderError
from reader.types import Entry
from discord_rss_bot.models import ConfigFile


class RSSReader:
    """Custom RSS reader class. Essentially an async wrapper around the reader library."""

    def __init__(self, config: ConfigFile):
        self.config = config
        self._init_reader()

    def _init_reader(self) -> None:
        """Initializes the reader."""
        logging.info("Initializing RSS reader")
        try:
            self.reader = make_reader(self.config.db_path)
        except ReaderError as e:
            logging.error("Error initializing reader: %s", e)
            raise

    async def setup(self) -> None:
        """
        Asynchronous setup that adds feeds, cleans up removed feeds,
        and updates feeds. This should be called after instantiating
        the class.
        """
        await self.add_feeds()
        await self.cleanup_removed_feeds()
        await self.update_feeds(scheduled=False)  # Immediate update after setup

    async def add_feeds(self) -> None:
        """Adds RSS feeds to the reader."""
        tasks = [
            self._add_feed(feed.feed_url, feed.update_interval)
            for feed in self.config.feeds
        ]
        await asyncio.gather(*tasks)  # Run all feed additions concurrently

    async def _add_feed(self, feed_url: str, update_interval: Optional[int]) -> None:
        """Helper function to add a single feed."""
        try:
            logging.info("Adding feed %s", feed_url)
            await self._execute_reader_task(
                self.reader.add_feed, feed_url, exist_ok=True
            )

            if update_interval:
                self.reader.set_tag(
                    feed_url, ".reader.update", {"interval": update_interval}
                )
        except ReaderError as e:
            logging.error("Error adding feed %s: %s", feed_url, e)

    async def update_feeds(self, scheduled: bool = True) -> None:
        """Updates the RSS feeds."""
        logging.info("Updating RSS Feeds (scheduled: %s)", scheduled)
        await self._execute_reader_task(self.reader.update_feeds, scheduled=scheduled)

    async def cleanup_removed_feeds(self) -> None:
        """Deletes RSS feeds removed from the config file."""
        config_feeds = {feed.feed_url for feed in self.config.feeds}
        reader_feeds = await self._get_existing_feeds()
        feeds_to_remove = reader_feeds - config_feeds

        tasks = [self._delete_feed(feed) for feed in feeds_to_remove]
        await asyncio.gather(*tasks)  # Run deletions concurrently

    async def _get_existing_feeds(self) -> Set[str]:
        """Helper function to retrieve existing feeds."""
        return (
            await self._execute_reader_task(
                lambda: {feed.url for feed in self.reader.get_feeds()}
            )
            or set()
        )

    async def _delete_feed(self, feed_url: str) -> None:
        """Helper function to delete a single feed."""
        try:
            logging.info("Removing feed: %s", feed_url)
            await self._execute_reader_task(self.reader.delete_feed, feed_url)
        except ReaderError as e:
            logging.error("Error removing feed %s: %s", feed_url, e)

    async def get_unread_entries(self, feed_url: str) -> List[Entry]:
        """Retrieve unread entries for a given feed."""
        logging.info("Fetching unread entries for %s", feed_url)
        entries = await self._execute_reader_task(
            lambda: list(self.reader.get_entries(feed=feed_url, read=False)), default=[]
        )
        return entries if entries is not None else []

    async def mark_entries_as_read(self, entries: List[Entry]) -> None:
        """Mark the provided list of entries as read."""
        if not entries:
            return

        logging.info("Marking %d entries as read", len(entries))
        tasks = [self._mark_entry_as_read(entry) for entry in entries]
        await asyncio.gather(*tasks)

    async def _mark_entry_as_read(self, entry: Entry) -> None:
        """Helper function to mark a single entry as read."""
        try:
            await self._execute_reader_task(self.reader.mark_entry_as_read, entry)
        except ReaderError as e:
            logging.error("Error marking entry '%s' as read: %s", entry.title, e)

    async def _execute_reader_task(self, func, *args, default=None, **kwargs):
        """
        Executes a function asynchronously with exception handling.
        Returns a default value if an error occurs.
        """
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except ReaderError as e:
            logging.error("Error executing task: %s", e)
            return default
