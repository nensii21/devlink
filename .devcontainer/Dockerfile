FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Install base packages, system tools, PostgreSQL & Redis client utilities
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*
