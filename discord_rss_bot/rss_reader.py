from discord_rss_bot.models import ConfigFile
import logging
import asyncio

from reader import make_reader, ReaderError
from reader.types import Entry
from typing import List


class RSSReader:
    def __init__(self, config: ConfigFile):
        self.config = config
        self._init_reader()

    def _init_reader(self) -> None:
        """Initializes the reader."""
        logging.info("Initializing RSS reader")
        try:
            self.reader = make_reader(self.config.db_path)
        except ReaderError as e:
            logging.error(f"Error initializing reader: {e}")
            raise

    async def setup(self) -> None:
        """
        Asynchronous setup that adds feeds, cleans up removed feeds,
        and updates feeds. This should be called after instantiating
        the class.
        """
        await self.add_feeds()
        await self.cleanup_removed_feeds()
        await self.update_feeds(scheduled=False)  # update feeds immediately

    async def add_feeds(self) -> None:
        """Adds RSS feeds to the reader."""
        try:
            for feed in self.config.feeds:
                logging.info(f"Adding feed {feed.feed_url}")
                await asyncio.to_thread(
                    self.reader.add_feed, feed.feed_url, exist_ok=True
                )
                if feed.update_interval:
                    self.reader.set_tag(
                        feed.feed_url,
                        ".reader.update",
                        {"interval": feed.update_interval},
                    )
        except ReaderError as e:
            logging.error(f"Error adding feeds: {e}")
            raise

    async def update_feeds(self, scheduled: bool = True) -> None:
        """Updates the RSS feeds."""
        try:
            logging.info(f"Updating RSS Feeds, scheduled: {scheduled}")
            await asyncio.to_thread(
                self.reader.update_feeds, scheduled=scheduled
            )
        except ReaderError as e:
            logging.error(f"Error updating feeds: {e}")
            raise

    async def cleanup_removed_feeds(self) -> None:
        """Deletes the RSS feeds removed from the config file."""
        config_feeds = {feed.feed_url for feed in self.config.feeds}
        # Offload the get_feeds call
        reader_feeds = await asyncio.to_thread(
            lambda: {feed.url for feed in self.reader.get_feeds()}
        )
        feeds_to_remove = reader_feeds - config_feeds

        for feed in feeds_to_remove:
            try:
                logging.info(f"Cleaning up removed feed: {feed}")
                await asyncio.to_thread(self.reader.delete_feed, feed)
            except ReaderError as e:
                logging.error(f"Error cleaning up removed feeds: {e}")
                raise

    async def get_unread_entries(self, feed_url: str) -> List[Entry]:
        """Retrieve unread entries for a given feed."""
        logging.info(f"Retrieving unread entries for feed {feed_url}")
        try:
            # Retrieve all unread entries as a list.
            unread_entries = await asyncio.to_thread(
                lambda: list(self.reader.get_entries(feed=feed_url, read=False))
            )
            logging.info(f"Retrieved {len(unread_entries)} unread entries")
            return unread_entries
        except ReaderError as e:
            logging.error(f"Error retrieving unread entries: {e}")
            raise

    async def mark_entries_as_read(self, entries: List) -> None:
        """Mark the provided list of entries as read."""
        logging.info(f"Marking {len(entries)} entries as read")
        for entry in entries:
            try:
                await asyncio.to_thread(self.reader.mark_entry_as_read, entry)
            except ReaderError as e:
                logging.error(
                    f"Error marking entry '{entry.title}' as read: {e}"
                )
                raise
