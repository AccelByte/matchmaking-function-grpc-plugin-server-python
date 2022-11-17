# AccelByte Plugin gRPC Architecture Demo - Server Component (Python)

## Prerequisites

* docker
* docker-compose
* make
* Python 3.9+

## Environment Variables

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

## Make

### Setting up the Virtual Environment

```shell
make setup
```

### Generate Proto Files

```
make generate
```

### Running Tests

```shell
make test
```

### Running the Server

```shell
make run
```

## Usage

Run dependencies first.

```shell
docker-compose -f docker-compose-dep.yml up
```

Run the app.

```shell
docker-compose -f docker-compose-app.yml up
```

Or (re)build and then run the app.

```shell
docker-compose -f docker-compose-app.yml up --build
```

## Useful Links

- [OpenTelemetry  > Instrumentation > Python](https://opentelemetry.io/docs/instrumentation/python)
- [Prometheus > Best Practices > Metric and Label Naming](https://prometheus.io/docs/practices/naming)
