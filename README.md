# discord-rss-bot

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![pylint score](./.github/badges/pylint.svg)](./.github/badges/pylint.svg)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Release](https://github.com/VioletCranberry/discord-rss-bot/actions/workflows/release.yaml/badge.svg)](https://github.com/VioletCranberry/discord-rss-bot/actions/workflows/release.yaml)

A Discord bot that delivers RSS feed updates in real-time to your servers.

Enpowered by [Feed Reader](https://github.com/lemon24/reader). Inspired by [FeedCord](https://github.com/Qolors/FeedCord).

## Features

- 🔄 Automated RSS Feed Updates – Periodic updates with configurable intervals.
- 📜 Enhanced Message Formatting – Attempts to convert HTML to Markdown, truncates long summaries without breaking formatting.
- 🖼️ Image & Media Support – Uses the first image as an embed cover for rich Discord embeds.
- ⚡ Efficient & Scalable – Optimized with async processing and concurrent execution.
- 🐋 Dockerized for Easy Deployment – Run anywhere with minimal setup.

## Configuration

1. Create a Discord bot and get its token.
2. Add the bot to your Discord server & channels.

The bot is configured via a YAML file. Here is an example:

```yaml

db_path: data/rss.sqlite3 # path to the database
feeds:

  # Releases of this project
  - feed_url: https://github.com/VioletCranberry/discord-rss-bot/releases.atom
    channel_id: 1336277462<redacted>
    update_interval: 30

  # Hacker news daily (Kudos to Colin Percival)
  - feed_url: https://www.daemonology.net/hn-daily/index.rss
    channel_id: 1334640995<redacted>
    update_interval: 30 # optional, defaults to 60 minutes if not provided

  # Ask hacker news weekly (Kudos to Colin Percival)
  - feed_url: https://www.daemonology.net/hn-weekly-ask/index.rss
    channel_id: 1335575467<redacted>
    update_interval: 30

  # Github - trending (all languages) daily
  - feed_url: https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml
    channel_id: 1336324646<redacted>
    update_interval: 30

  # Github - trending (all languages) weekly
  - feed_url: https://mshibanami.github.io/GitHubTrendingRSS/weekly/all.xml
    channel_id: 1336383236<redacted>
    update_interval: 30

    # Hacker News Best - top vote getters from the past few days
  - feed_url: https://hnrss.org/best
    channel_id: 1335577844<redacted>
    update_interval: 30

  ...
```

## Docker run

```bash
docker run \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/data:/app/data \
  ghcr.io/violetcranberry/discord-rss-bot:latest
```

## Docker compose

```yaml
discord-rss-bot:
  image: ghcr.io/violetcranberry/discord-rss-bot:latest
  container_name: discord-rss-bot
  environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
  volumes:
    - ./config.yaml:/app/config.yaml
    - ./data:/app/data
  restart: unless-stopped
  # command:
    #   - "--token=${DISCORD_BOT_TOKEN}"
    #   - "--debug"
```

## Local development

```bash
git clone https://github.com/VioletCranberry/discord-rss-bot.git && cd discord-rss-bot
poetry install --with dev

poetry run python -m discord_rss_bot <args>
poetry run pylint --verbose discord_rss_bot
poetry run black --verbose discord_rss_bot
```
