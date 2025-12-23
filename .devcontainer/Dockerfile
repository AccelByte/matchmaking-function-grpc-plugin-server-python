# Development container for AccelByte Extend Service Extension
FROM ubuntu:22.04

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

ARG PROTOC_VERSION=21.9
ARG PYTHON_VERSION=3.10
ARG EXTEND_HELPER_CLI_VERSION=0.0.9

# Configure apt and install packages
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    #
    # Install essential development tools
    build-essential \
    ca-certificates \
    sudo \
    unzip \
    wget \
    #
    # Install Python and pip
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    #
    # Install Protocol Buffers compiler
    && wget -O protoc.zip https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip \
    && unzip protoc.zip -d /usr/local \
    && rm protoc.zip \
    && chmod +x /usr/local/bin/protoc \
    #
    # Install Extend Helper CLI
    && wget -O /usr/local/bin/extend-helper-cli https://github.com/AccelByte/extend-helper-cli/releases/download/v${EXTEND_HELPER_CLI_VERSION}/extend-helper-cli-linux_amd64 \
    && chmod +x /usr/local/bin/extend-helper-cli \
    #
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set up Python symlinks
RUN ln -sf /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python3 \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create user group, user account, and configure passwordless sudo access
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Switch to non-root user
USER $USERNAME

# Install Python development tools
RUN pip install --user grpcio-tools==1.76.0 mypy-protobuf==4.0.0 fillenv==1.0.0

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

WORKDIR /workspace
