# ---- Main Image --------------------------------------------------------------
FROM ubuntu:24.04

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl git nano openssh-client make libatomic1 bash-completion \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER ubuntu

# Install uv
ENV UV_VERSION=0.9.4
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh
