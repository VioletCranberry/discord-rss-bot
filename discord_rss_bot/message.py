from reader.types import Entry
from markdownify import markdownify as md
from bs4 import BeautifulSoup

import discord
import logging


def truncate_html(html: str, length: int = 3000):
    """Safely truncates provided HTML string."""
    if len(html) <= length:
        return html
    return str(
        BeautifulSoup(html[:length] + "... (truncated)", features="html.parser")
    )


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
    if hasattr(entry, "summary") and entry.summary:
        summary_md = truncate_html(entry.summary)
        summary_md = convert_html_to_markdown(summary_md)

    embed = discord.Embed(
        title=title, url=entry.link, color=discord.Color.blue()
    )
    if summary_md:
        embed.description = f"💬 **Summary:** \n\n {summary_md}"
    else:
        embed.description = f"💬 **Summary:** \n\n No Summary Provided"

    if hasattr(entry, "published") and entry.published:
        embed.timestamp = entry.published

    embed.set_footer(text=f"🔗 {entry.feed_url} 🔗")
    return embed
