FROM python:3.13.1-slim-bullseye AS builder

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache \
  PIP_NO_CACHE_DIR=on \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

WORKDIR /app
RUN pip install poetry==2.0.1

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.13.1-slim-bullseye AS runtime

ENV VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH" \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1

RUN groupadd -g 1001 python \
  && useradd --create-home --no-log-init -u 1001 -g 1001 python

USER python
WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY discord_rss_bot ./discord_rss_bot 
ENTRYPOINT ["python", "-m", "discord_rss_bot"]
