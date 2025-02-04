from reader.types import Entry
import html2text

import discord
import logging


def convert_html_to_markdown(html: str) -> str:
    """Converts an HTML string into Markdown format using html2text."""
    try:
        converter = html2text.HTML2Text()
        # Preserve links in the output.
        converter.ignore_links = False
        # Disasble line wrapping.
        converter.body_width = 0
        # Convert the HTML content to Markdown.
        markdown_text = converter.handle(html).strip()
        # Remove empty lines & apply Discord block quotes.
        formatted_text = "\n".join(
            f"> {line}" for line in markdown_text.splitlines() if line.strip()
        )
        return formatted_text
    except Exception as e:
        logging.error("Error converting HTML to Markdown: %s", e)
        # Return the original HTML as a fallback.
        return html


def format_entry_for_discord(entry: Entry) -> discord.Embed:
    """Formats a single RSS entry into a discord.Embed."""
    logging.debug("Formatting entry")

    title = f"📰 {entry.title}"
    # Convert the HTML summary to Markdown.
    summary_md = ""
    if hasattr(entry, "summary") and entry.summary:
        summary_md = convert_html_to_markdown(entry.summary)

    embed = discord.Embed(
        title=title, url=entry.link, color=discord.Color.blue()
    )
    # Add the summary as a description.
    if summary_md:
        embed.description = f"💬 Summary: \n {summary_md[:4096]}"
    else:
        embed.description = f"💬 No Summary Provided"
    embed.set_footer(text=f"Source: {entry.feed_url} 🔗")
    return embed
