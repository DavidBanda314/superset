# Keep this in sync with the base image in the main Dockerfile (ARG PY_VER)
FROM python:3.11.13-trixie AS base

# Install system dependencies that Superset needs
# This layer will be cached across Codespace sessions
RUN apt-get update && apt-get install -y \
    libsasl2-dev \
    libldap2-dev \
    libpq-dev \
    tmux \
    gh \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management from PyPI at a pinned version,
# rather than piping a remote installer script into a root shell
# This will also be cached in the image
ARG UV_VERSION=0.11.32
RUN pip install --no-cache-dir "uv==${UV_VERSION}"
