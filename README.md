# discord-rss-bot

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![pylint score](./.github/badges/pylint.svg)](./.github/badges/pylint.svg)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

A Discord bot that delivers RSS feed updates in real-time. Work in progress.

Enpowered by [Feed Reader](https://github.com/lemon24/reader).

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
poetry install --with dev

poetry run python -m discord_rss_bot <args>
poetry run pylint --verbose discord_rss_bot
poetry run black --verbose discord_rss_bot
```
