FROM python:3.10-slim
WORKDIR /data
RUN apt update && apt install -y bash curl git jq make xxd \
        && apt clean \
        && rm -rf /var/lib/apt/lists/*
RUN curl 'https://download.docker.com/linux/debian/dists/bookworm/pool/stable/amd64/docker-ce-cli_23.0.6-1~debian.12~bookworm_amd64.deb' -o /tmp/docker-ce-cli.deb \
        && curl 'https://download.docker.com/linux/debian/dists/bookworm/pool/stable/amd64/docker-buildx-plugin_0.11.2-1~debian.12~bookworm_amd64.deb' -o /tmp/docker-buildx-plugin.deb \
        && dpkg -i /tmp/docker-ce-cli.deb /tmp/docker-buildx-plugin.deb \
        && rm -f /tmp/docker-ce-cli.deb /tmp/docker-buildx-plugin.deb
COPY --from=ngrok/ngrok /bin/ngrok /bin/ngrok
