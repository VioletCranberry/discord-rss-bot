"""Models for the bot configuration file."""

from typing import List, Optional
from pydantic import BaseModel


class FeedConfig(BaseModel):
    """Configuration for a single RSS feed."""

    feed_url: str
    channel_id: int | str
    update_interval: Optional[int]


class ConfigFile(BaseModel):
    """Configuration file for the bot."""

    db_path: str
    feeds: List[FeedConfig]
