# Copyright (c) 2025 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

# ----------------------------------------
# Stage 1: Protoc Code Generation
# ----------------------------------------
FROM --platform=$BUILDPLATFORM rvolosatovs/protoc:4.1.0 AS proto-builder

# Set working directory.
WORKDIR /build

# Copy proto sources and generator script.
COPY proto.sh .
COPY proto/ proto/

# Make script executable and run it.
RUN chmod +x proto.sh && \
    ./proto.sh



# ----------------------------------------
# Stage 2: Builder
# ----------------------------------------
FROM ubuntu:22.04 AS builder

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
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group
COPY --from=builder /build/ .

USER user

# Activate virtual environment.
ENV PATH="/app/venv/bin:$PATH"

# Plugin Arch gRPC Server Port.
EXPOSE 6565

# Prometheus /metrics Web Server Port.
EXPOSE 8080

# Entrypoint.
ENTRYPOINT ["python3", "-m", "app"]
