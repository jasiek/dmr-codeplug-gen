FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye
RUN apt-get update
RUN apt install -y curl make
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
