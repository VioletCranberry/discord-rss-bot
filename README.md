# discord-rss-bot

A Discord bot that delivers RSS feed updates in real-time. Work in progress.

## Docker usage

```bash
docker run -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/rss.sqlite3:/app/rss.sqlite3 \
  ghcr.io/violetcranberry/discord-rss-bot:latest
```

## Docker Compose usage

```yaml
discord-rss-bot:
  image: ghcr.io/violetcranberry/discord-rss-bot:latest
  container_name: discord-rss-bot
  environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
  volumes:
    - ./config.yaml:/app/config.yaml
    - ./rss.sqlite3:/app/rss.sqlite3
  restart: unless-stopped
  # command:
    #   - "--token=${DISCORD_BOT_TOKEN}"
    #   - "--debug"
```
