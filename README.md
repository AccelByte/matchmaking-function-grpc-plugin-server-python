# AccelByte Plugin gRPC Architecture Demo - Server Component (Python)

## Prerequisites

* docker-compose
* make
* Python 3.9

## Environment Variables

| Environment Variable           | Description                                                                                                             |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| APP_NAME                       | Used as the service name and the User-Agent for AccelByte endpoints.                                                    |
| APP_SECURITY_BASE_URL          | ex: `APP_SECURITY_BASE_URL=http://demo.accelbyte.io`                                                                    |
| APP_SECURITY_CLIENT_ID         | AccelByte Username for HTTP basic auth.                                                                                 |
| APP_SECURITY_CLIENT_SECRET     | AccelByte Password for HTTP basic auth.                                                                                 |
| APP_SECURITY_NAMESPACE         | Falls back to `NAMESPACE` if not found. default: `accelbyte`                                                            |
| APP_SECURITY_RESOURCE_NAME     | default: `MMV2GRPCSERVICE`                                                                                              |
| ENABLE_INTERCEPTOR_AUTH        | ex: `ENABLE_INTERCEPTOR_AUTH=1` default: `1`                                                                            |
| ENABLE_INTERCEPTOR_DEBUG       | ex: `ENABLE_INTERCEPTOR_DEBUG=1` default: `1`                                                                           |
| ENABLE_LOKI                    | ex: `ENABLE_LOKI=1` default: `1`                                                                                        |
| ENABLE_ZIPKIN                  | ex: `ENABLE_ZIPKIN=1` default: `1`                                                                                      |
| LOKI_URL                       | ex: `LOKI_URL=http://loki:3100/loki/api/v1/push`                                                                        |
| LOKI_USERNAME                  | Loki Username for HTTP basic auth.                                                                                      |
| LOKI_PASSWORD                  | Loki Password for HTTP basic auth.                                                                                      |
| OTEL_EXPORTER_ZIPKIN_ENDPOINT  | Endpoint for Zipkin traces. default: `http://localhost:9411/api/v2/spans`                                               |
| OTEL_EXPORTER_ZIPKIN_TIMEOUT   | Maximum time (in milliseconds) the Zipkin exporter will wait for each batch export. default: `10000`                    |
| TOKEN_VALIDATOR_FETCH_INTERVAL | How often to refetch the JWKS and Revocation List (in seconds) ex: `TOKEN_VALIDATOR_FETCH_INTERVAL=300` default: `3600` |

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

## Using with Make

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
