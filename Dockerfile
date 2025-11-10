# Copyright (c) 2025 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

# ----------------------------------------
# Stage 1: Protoc Code Generation
# ----------------------------------------
FROM --platform=$BUILDPLATFORM ubuntu:22.04 AS proto-builder

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

ARG PROTOC_VERSION=21.9
ARG PYTHON_VERSION=3.10

# Configure apt and install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    #
    # Install essential development tools
    build-essential \
    ca-certificates \
    unzip \
    wget \
    #
    # Install Python and pip
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    #
    # Detect architecture for downloads
    && ARCH_SUFFIX=$(case "$(uname -m)" in \
        x86_64) echo "x86_64" ;; \
        aarch64) echo "aarch_64" ;; \
        *) echo "x86_64" ;; \
       esac) \
    #
    # Install Protocol Buffers compiler
    && wget -O protoc.zip https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-${ARCH_SUFFIX}.zip \
    && unzip protoc.zip -d /usr/local \
    && rm protoc.zip \
    && chmod +x /usr/local/bin/protoc \
    #
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set up Python symlinks
RUN ln -sf /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python3 \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip

# Install Python tools required for proto generation.
RUN pip install --no-cache-dir grpcio-tools==1.76.0 mypy-protobuf==3.6.0

# Set working directory.
WORKDIR /build

# Copy proto sources and generator script.
COPY proto.sh .
COPY proto/ proto/

# Make script executable and run it.
RUN chmod +x proto.sh && \
    ./proto.sh



# ----------------------------------------
# Stage 2: gRPC Server Builder
# ----------------------------------------
FROM ubuntu:22.04 AS grpc-server-builder

# Keeps Python from generating .pyc files in the container.
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging.
ENV PYTHONUNBUFFERED=1

# Install Python.
RUN apt update && \
    apt install -y --no-install-recommends \
        python3-venv && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd user

# Set working directory.
WORKDIR /build

# Create and activate virtual environment.
RUN python3 -m venv venv
ENV PATH="/build/venv/bin:$PATH"

# Install Python dependencies.
COPY requirements.txt .
RUN python3 -m pip install \
    --no-cache-dir \
    --requirement requirements.txt

# Copy application code.
COPY src/ .

# Copy generated protobuf files from stage 1.
COPY --from=proto-builder /build/src/ . 

# Fix up python3 symlink for use in chiseled Ubuntu.
RUN ln -sf /usr/bin/python3 /build/venv/bin/python3 



# ----------------------------------------
# Stage 3: Runtime Container
# ----------------------------------------
FROM ubuntu/python:3.10-22.04_stable

# Keeps Python from generating .pyc files in the container.
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging.
ENV PYTHONUNBUFFERED=1

# Set working directory.
WORKDIR /app

# Copy build from stage 2.
COPY --from=grpc-server-builder /usr/bin/bash /usr/bin/bash
COPY --from=grpc-server-builder /usr/bin/kill /usr/bin/kill
COPY --from=grpc-server-builder /usr/bin/sleep /usr/bin/sleep
COPY --from=grpc-server-builder /etc/passwd /etc/passwd
COPY --from=grpc-server-builder /etc/group /etc/group
COPY --from=grpc-server-builder /build/ .

USER user

# Activate virtual environment.
ENV PATH="/app/venv/bin:$PATH"

# Plugin Arch gRPC Server Port.
EXPOSE 6565

# Prometheus /metrics Web Server Port.
EXPOSE 8080

# Entrypoint.
ENTRYPOINT ["python3", "-m", "app"]
