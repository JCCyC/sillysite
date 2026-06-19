# Dev Container image: everything needed to edit, run, and test SillySite
# interactively (Python, the C and JS bindings' toolchains, and a browser
# for the static-pages test). Built on the standard Dev Containers base
# image, which already sets up the non-root `vscode` user that
# devcontainer.json's "remoteUser" expects.
FROM mcr.microsoft.com/devcontainers/base:debian-12

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        build-essential \
        libcurl4-openssl-dev \
        libssl-dev \
        libcjson-dev \
        pkg-config \
        postgresql-client \
        chromium \
        chromium-driver \
        jq \
    && rm -rf /var/lib/apt/lists/*
