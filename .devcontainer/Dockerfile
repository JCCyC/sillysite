# Dev Container image: everything needed to edit, run, and test SillySite
# interactively (Python, the C, JS, Java, C#, and PHP bindings' toolchains,
# and a browser for the static-pages test). Built on the standard Dev
# Containers base image, which already sets up the non-root `vscode` user
# that devcontainer.json's "remoteUser" expects.
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
        openjdk-17-jdk-headless \
        mono-complete \
        php-cli \
        jq \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

# mono-complete (csharp/) is the same upstream Mono release (6.8.0.105) as
# Ubuntu 22.04's -- the base of Linux Mint 21.x, this project's other
# target environment -- confirmed by hand to install cleanly there too with
# no extra repository (no Mono Project PPA needed on either distro). See
# csharp/README-CSHARP.md.

# docker.io bundles a dockerd binary we never run -- only the `docker` CLI
# is needed here, to talk to the *host's* daemon over the socket
# docker-compose.yml bind-mounts in (Docker-outside-of-Docker, so
# tests/run_tests.sh can drive Docker from inside this container). Not using
# the official docker-outside-of-docker devcontainer Feature for this: that
# feature hardcodes mounting the host's socket from the conventional
# /var/run/docker.sock path, which doesn't exist on a host running rootless
# Docker (this one does) -- and that hardcoded path can't be overridden from
# project files, since the feature's own auto-generated compose override is
# merged in last and always wins over anything declared here. Doing the CLI
# install ourselves sidesteps that entirely.
