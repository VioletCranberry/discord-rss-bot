"""
Data models for the bot configuration file.

These models define the structure of the bot's configuration,
including RSS feed details and database settings.

Uses Pydantic for data validation and structured parsing.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FeedConfig(BaseModel):
    """Represents the configuration for a single RSS feed."""

    feed_url: str = Field(..., description="The URL of the RSS feed.")
    channel_id: int | str = Field(
        ..., description="The Discord channel ID for posting updates."
    )
    update_interval: Optional[int] = Field(
        None, description="Update interval in minutes (if set)."
    )


class ConfigFile(BaseModel):
    """Represents the main configuration file for the bot."""

    db_path: str = Field(..., description="Path to the SQLite database file.")
    feeds: List[FeedConfig] = Field(
        ..., description="List of configured RSS feeds."
    )
