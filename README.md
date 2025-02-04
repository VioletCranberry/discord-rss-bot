# discord-rss-bot

A Discord bot that delivers RSS feed updates in real-time. Work in progress.

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
