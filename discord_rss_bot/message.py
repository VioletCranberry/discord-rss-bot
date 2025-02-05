"""
Discord message formatting functions for RSS feed entries.

This module provides functions to:
- Convert HTML content to Markdown.
- Extract and handle images in summaries.
- Format RSS entries into `discord.Embed` messages for posting.
"""

import logging

from reader.types import Entry
from markdownify import markdownify as md
from bs4 import BeautifulSoup
import discord


def truncate_html(html: str, length: int = 3000):
    """Safely truncates provided HTML string."""
    if len(html) <= length:
        return html

    soup = BeautifulSoup(html[:length], "html.parser")
    # Append a truncation indicator inside a <strong> tag
    truncated_tag = soup.new_tag("strong")
    truncated_tag.string = " ... (truncated)"
    soup.append(truncated_tag)
    return str(soup)


def extract_images_from_html(html: str):
    """Extracts image URLs from an HTML string."""
    soup = BeautifulSoup(html, features="html.parser")
    images = [
        img.attrs["src"]  # pyright: ignore[reportAttributeAccessIssue]
        for img in soup.find_all("img")
        if "src" in img.attrs  # pyright: ignore[reportAttributeAccessIssue]
    ]
    return images


def convert_html_to_markdown(html: str) -> str:
    """Converts an HTML string into Markdown format."""
    markdown_text = md(html, heading_style="ATX").strip()
    formatted_text = "\n".join(
        f"> {line}" for line in markdown_text.splitlines() if line.strip()
    )
    return formatted_text


def format_entry_for_discord(entry: Entry) -> discord.Embed:
    """Formats a single RSS entry into a discord.Embed."""
    logging.debug("Formatting entry")

    title = f"📰 {entry.title}"
    summary_md = ""
    image_urls = []
    if hasattr(entry, "summary") and entry.summary:
        truncated_summary = truncate_html(entry.summary)
        image_urls = extract_images_from_html(
            truncated_summary
        )  # Extract images first
        summary_md = convert_html_to_markdown(
            truncated_summary
        )  # Convert to Markdown

    embed = discord.Embed(
        title=title, url=entry.link, color=discord.Color.blue()
    )
    embed.description = (
        f"💬 **Summary:**\n\n{summary_md}"
        if summary_md
        else "💬 **Summary:**\n\n_No Summary Provided_"
    )

    if hasattr(entry, "published") and entry.published:
        embed.timestamp = entry.published

    embed.set_footer(text=f"🔗 {entry.feed_url} 🔗")
    if image_urls:
        embed.set_image(url=image_urls[0])
    return embed
