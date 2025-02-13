"""
RSSReader: An Asynchronous RSS Feed Manager for Discord Bots.

This module implements an asynchronous wrapper around the `reader` library,
designed specifically to manage RSS feeds efficiently in a non-blocking
manner for Discord bots.

Key responsibilities include:
  - Feed Management: Adding new feeds, updating existing feeds, and
    removing feeds that are no longer in the configuration.
  - Entry Processing: Retrieving unread entries from feeds and marking
    them as read after processing.
  - Asynchronous Execution: Offloading blocking operations to a separate
    thread using `asyncio.to_thread()`, ensuring that feed operations do not
    block the main event loop.
  - Separation of Concerns: Delegating asynchronous task execution and
    feed-specific helper functions to dedicated classes for improved
    maintainability and testability.

This design enables efficient and scalable integration of RSS feed updates
into Discord bots, providing a robust data layer that can handle frequent
feed updates and entry processing without impacting the responsiveness of
the application.
"""

import asyncio
import logging
from typing import Any, Callable, List, Optional, Set, TypeVar

from reader import Reader, ReaderError, make_reader
from reader.types import Entry

from discord_rss_bot.models import ConfigFile

T = TypeVar("T")


# pylint: disable=too-few-public-methods
class ReaderTaskExecutor:
    """Helper class that runs blocking reader tasks in a separate thread."""

    def __init__(self, rss_reader: Reader) -> None:
        self.rss_reader = rss_reader

    async def run(
        self,
        func: Callable[..., T],
        *args: Any,
        default: Optional[T] = None,
        **kwargs: Any,
    ) -> Optional[T]:
        """Runs a blocking reader task in a separate thread."""
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except ReaderError as error:
            logging.error("Error executing task: %s", error)
            return default


class FeedManager:
    """Encapsulates feed operations and manages RSS feed interactions using the reader"""

    def __init__(
        self, rss_reader: Reader, executor: ReaderTaskExecutor
    ) -> None:
        self.rss_reader = rss_reader
        self.executor = executor

    async def add_feed(
        self, feed_url: str, update_interval: Optional[int]
    ) -> None:
        """Adds a single feed and sets the update interval if provided."""
        try:
            logging.info("Adding feed: %s", feed_url)
            await self.executor.run(
                self.rss_reader.add_feed, feed_url, exist_ok=True
            )
            if update_interval is not None:
                self.rss_reader.set_tag(
                    feed_url, ".reader.update", {"interval": update_interval}
                )
        except ReaderError as error:
            logging.error("Error adding feed %s: %s", feed_url, error)

    async def update_feeds(self, scheduled: bool = True) -> None:
        """Updates all RSS feeds."""
        logging.info("Updating RSS feeds (scheduled=%s)", scheduled)
        await self.executor.run(
            self.rss_reader.update_feeds, scheduled=scheduled
        )

    async def get_existing_feeds(self) -> Set[str]:
        """Retrieves the set of feed URLs currently registered in the reader."""
        feeds = await self.executor.run(
            lambda: {feed.url for feed in self.rss_reader.get_feeds()}
        )
        return feeds if feeds is not None else set()

    async def delete_feed(self, feed_url: str) -> None:
        """Deletes a feed from the reader."""
        try:
            logging.info("Removing feed: %s", feed_url)
            await self.executor.run(self.rss_reader.delete_feed, feed_url)
        except ReaderError as error:
            logging.error("Error removing feed %s: %s", feed_url, error)

    async def get_unread_entries(self, feed_url: str) -> List[Entry]:
        """Retrieves unread entries for a given feed."""
        logging.info("Fetching unread entries for %s", feed_url)
        entries = await self.executor.run(
            lambda: list(
                self.rss_reader.get_entries(feed=feed_url, read=False)
            ),
            default=[],
        )
        return entries if entries is not None else []

    async def mark_entry_as_read(self, entry: Entry) -> None:
        """Marks a single entry as read."""
        try:
            await self.executor.run(self.rss_reader.mark_entry_as_read, entry)
        except ReaderError as error:
            logging.error(
                "Error marking entry '%s' as read: %s", entry.title, error
            )

    async def mark_entries_as_read(self, entries: List[Entry]) -> None:
        """Marks the provided list of entries as read."""
        if not entries:
            return

        logging.info("Marking %d entries as read", len(entries))
        tasks = [self.mark_entry_as_read(entry) for entry in entries]
        await asyncio.gather(*tasks)

    async def cleanup_removed_feeds(self, config_feeds: Set[str]) -> None:
        """Removes feeds from the reader that are not in the provided configuration."""
        existing_feeds = await self.get_existing_feeds()
        feeds_to_remove = existing_feeds - config_feeds

        if feeds_to_remove:
            tasks = [self.delete_feed(feed_url) for feed_url in feeds_to_remove]
            await asyncio.gather(*tasks)


class RSSReader:
    """
    Asynchronous wrapper around the reader library for managing RSS feeds.
    1. Delegates feed operations to FeedManager.
    2. Delegates blocking tasks to ReaderTaskExecutor.
    """

    def __init__(self, config: ConfigFile) -> None:
        self.config = config
        self._init_reader()

        self.task_executor = ReaderTaskExecutor(self.reader)
        self.feed_manager = FeedManager(self.reader, self.task_executor)

    def _init_reader(self) -> None:
        """Initializes the underlying reader instance."""
        logging.info("Initializing RSS reader")
        try:
            self.reader = make_reader(self.config.db_path)
        except ReaderError as error:
            logging.error("Error initializing reader: %s", error)
            raise

    async def add_feeds(self) -> None:
        """Adds all feeds specified in the configuration."""
        tasks = [
            self.feed_manager.add_feed(feed.feed_url, feed.update_interval)
            for feed in self.config.feeds
        ]
        await asyncio.gather(*tasks)

    async def update_feeds(self, scheduled: bool = True) -> None:
        """Updates the RSS feeds."""
        await self.feed_manager.update_feeds(scheduled=scheduled)

    async def cleanup_removed_feeds(self) -> None:
        """Removes feeds that are no longer in the configuration."""
        config_feeds = {feed.feed_url for feed in self.config.feeds}
        await self.feed_manager.cleanup_removed_feeds(config_feeds)

    async def get_unread_entries(self, feed_url: str) -> List[Entry]:
        """Retrieves unread entries for a specified feed."""
        return await self.feed_manager.get_unread_entries(feed_url)

    async def mark_entries_as_read(self, entries: List[Entry]) -> None:
        """Marks specified entries as read."""
        await self.feed_manager.mark_entries_as_read(entries)

    async def setup(self) -> None:
        """
        Asynchronously sets up the RSS feeds by:
        1. Adding new feeds
        2. Cleaning up removed feeds
        3. Performing an initial update.
        """
        await asyncio.gather(self.add_feeds(), self.cleanup_removed_feeds())
        # Immediate update after setup
        await self.update_feeds(scheduled=False)
