# plugin-arch-grpc-server-python

> :warning: **If you are new to AccelByte Cloud Service Customization gRPC Plugin Architecture**: Start reading from `OVERVIEW.md` in `plugin-arch-grpc-dependencies` repository to get the full context.

AccelByte Cloud service customization using gRPC plugin architecture - Server (Python).

## Prerequisites

1. Windows 10 WSL2 or Linux Ubuntu 20.04 with the following tools installed.

    a. bash

    b. docker

    c. docker-compose

    d. make

    e. python 3.9+

2. AccelByte Cloud demo environment.

    a. Base URL: https://demo.accelbyte.io.

    b. [Create a Game Namespace](https://docs.accelbyte.io/esg/uam/namespaces.html#tutorials) if you don't have one yet. Keep the `Namespace ID`.

    c. [Create an OAuth Client](https://docs.accelbyte.io/guides/access/iam-client.html) with confidential client type and give it `read` permission to resource `NAMESPACE:{namespace}:MMV2GRPCSERVICE`. Keep the `Client ID` and `Client Secret`.

## Setup

Create a docker compose `.env` file based on `.env.template` file and fill in the required environment variables in `.env` file.

```
APP_SECURITY_BASE_URL=https://demo.accelbyte.io     # Base URL
APP_SECURITY_CLIENT_ID=xxxxxxxxxx                   # Client ID
APP_SECURITY_CLIENT_SECRET=xxxxxxxxxx               # Client Secret
NAMESPACE=xxxxxxxxxx                                # Namespace ID
```

> :exclamation: **For the server and client**: Use the same Base URL, Client ID, Client Secret, and Namespace ID.

## Developing

Helper commands to make development easier.

```
make setup      # Setting up virtual environment
make build      # Generating code from proto files
make test       # Running tests
make run        # Running the server (without container)
```

For more details about the command, see [Makefile](Makefile).

## Building

Build the project and create a docker image for the current platform in one go.

```
make build image
```
For more details about the command, see [Makefile](Makefile).

## Running

Use the following command to run the project in a container.

```
docker-compose up
```

## Advanced

### Building Multi-Arch Docker Image

Build the project and create a multi-arch docker image in one go.

```
make build imagex
```

For more details about the command, see [Makefile](Makefile).

### Environment Variables

| Environment Variable           | Description                                                                         | Default                                  |
|--------------------------------|-------------------------------------------------------------------------------------|------------------------------------------|
| APP_NAME                       | Used as the service name and the User-Agent for AccelByte endpoints.                | `app-server`                             |
| APP_SECURITY_BASE_URL          | AccelByte HTTP base url.                                                            | `https://demo.accelbyte.io`              |
| APP_SECURITY_CLIENT_ID         | AccelByte Username for HTTP basic auth.                                             |                                          |
| APP_SECURITY_CLIENT_SECRET     | AccelByte Password for HTTP basic auth.                                             |                                          |
| APP_SECURITY_NAMESPACE         | Also checks env-var `NAMESPACE` if not found.                                       | `accelbyte`                              |
| APP_SECURITY_RESOURCE_NAME     |                                                                                     | `MMV2GRPCSERVICE`                        |
| ENABLE_INTERCEPTOR_AUTH        |                                                                                     | `true`                                   |
| ENABLE_INTERCEPTOR_LOGGING     |                                                                                     | `true`                                   |
| ENABLE_INTERCEPTOR_METRICS     |                                                                                     | `true`                                   |
| ENABLE_LOKI                    |                                                                                     | `true`                                   |
| ENABLE_PROMETHEUS              |                                                                                     | `true`                                   |
| ENABLE_ZIPKIN                  |                                                                                     | `true`                                   |
| LOKI_URL                       |                                                                                     | `http://localhost:3100/loki/api/v1/push` |
| LOKI_USERNAME                  | Loki Username for HTTP basic auth.                                                  |                                          |
| LOKI_PASSWORD                  | Loki Password for HTTP basic auth.                                                  |                                          |
| OTEL_EXPORTER_ZIPKIN_ENDPOINT  | Endpoint for Zipkin traces.                                                         | `http://localhost:9411/api/v2/spans`     |
| OTEL_EXPORTER_ZIPKIN_TIMEOUT   | Maximum time (in milliseconds) the Zipkin exporter will wait for each batch export. | `10000`                                  |
| PROMETHEUS_ADDR                | Prometheus HTTP server address.                                                     | `0.0.0.0`                                |
| PROMETHEUS_PORT                | Prometheus HTTP server port.                                                        | `8080`                                   |
| PROMETHEUS_ENDPOINT            | Prometheus endpoint.                                                                | `/metrics`                               |
| PROMETHEUS_PREFIX              | Prometheus prefix.                                                                  | `$(camelcase APP_NAME)`                  |
| TOKEN_VALIDATOR_FETCH_INTERVAL | How often to refetch the JWKS, Revocation List, and Role List (in seconds).         | `3600`                                   |

### Useful Links

- [OpenTelemetry  > Instrumentation > Python](https://opentelemetry.io/docs/instrumentation/python)
- [Prometheus > Best Practices > Metric and Label Naming](https://prometheus.io/docs/practices/naming)
