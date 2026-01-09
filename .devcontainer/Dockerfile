# ---- Verilator Builder -------------------------------------------------------
FROM ubuntu:24.04 as verilator_builder

# Setup environment variables
ENV VERILATOR_VERSION=v5.042 \
    VERILATOR_INSTALL=/opt/verilator

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates git \
    help2man perl python3 make autoconf g++ mold flex bison ccache libfl2 libfl-dev

# Build Verilator
RUN git clone --branch ${VERILATOR_VERSION} --depth 1 https://github.com/verilator/verilator.git
RUN cd verilator && \
    autoconf && \
    ./configure --prefix ${VERILATOR_INSTALL} && \
    make -j$(nproc) && \
    make install

# ---- slang-server Builder -------------------------------------------------------
FROM ubuntu:24.04 AS slang_server_builder

# Setup environment variables
ENV SLANG_SERVER_VERSION=v0.2.1 \
    SLANG_SERVER_INSTALL=/opt/slang-server

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates git cmake g++ ninja-build python3 python3-dev

# Clone the repository and build
RUN git clone --branch ${SLANG_SERVER_VERSION} --depth 1 https://github.com/hudson-trading/slang-server.git && \
    cd slang-server && \
    git submodule update --init --recursive --depth 1 && \
    cmake -B build -DCMAKE_BUILD_TYPE=Release -G Ninja && \
    cmake --build build --target slang_server && \
    mkdir -p ${SLANG_SERVER_INSTALL}/bin && \
    cp build/bin/slang-server ${SLANG_SERVER_INSTALL}/bin/

# ---- Main Image --------------------------------------------------------------
FROM ubuntu:24.04

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl git nano openssh-client make libatomic1 bash-completion \
    g++ mold ccache perl-doc z3 gtkwave \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Verilator
ENV VERILATOR_INSTALL=/opt/verilator
COPY --from=verilator_builder ${VERILATOR_INSTALL} ${VERILATOR_INSTALL}

# Install slang-server
ENV SLANG_SERVER_INSTALL=/opt/slang-server
COPY --from=slang_server_builder ${SLANG_SERVER_INSTALL} ${SLANG_SERVER_INSTALL}

# Add user rights to access the install directories
RUN chown -R ubuntu:ubuntu /opt

# Install Codex
RUN npm i -g @openai/codex

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

# Switch to non-root user
USER ubuntu

# Install uv
ENV UV_VERSION=0.9.4
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh

# Update PATH
ENV PATH="${HOME}/.local/bin:${VERILATOR_INSTALL}/bin:${SLANG_SERVER_INSTALL}/bin:${PATH}"
