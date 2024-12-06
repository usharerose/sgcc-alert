FROM python:3.10-slim AS builder

MAINTAINER Chaojie Yan

# Setup basic Linux packages
RUN apt update && \
    apt install -y tini tzdata build-essential libffi-dev make && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app/sgcc-alert/

COPY . .

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.8.3 \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    # no virtual env need for container
    POETRY_VIRTUALENVS_CREATE=false

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$PATH"
# Add PYTHONPATH
ENV PYTHONPATH /app/sgcc-alert/

# install dependencies
RUN python -m pip install --no-cache --upgrade pip && \
    python -m pip install --no-cache poetry==${POETRY_VERSION} && \
    poetry install && \
    python -m playwright install --with-deps && \
    find /usr/local/ -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

FROM python:3.10-slim AS dev

COPY --from=builder /etc/ /etc/
COPY --from=builder /usr/ /usr/
COPY --from=builder /app/sgcc-alert/ /app/sgcc-alert/
COPY --from=builder /root/.cache/ms-playwright/ /root/.cache/ms-playwright/

# Set workdir
WORKDIR /app/sgcc-alert/

# Tini is now available
ENTRYPOINT ["/usr/bin/tini", "--"]
