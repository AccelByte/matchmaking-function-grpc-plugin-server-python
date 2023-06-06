import asyncio
import logging
import os

from argparse import ArgumentParser
from logging import Logger
from typing import Any, List, Optional, Union

import grpc.aio

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import aio_server_interceptor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

import app.logger

import app.proto.matchFunction_pb2 as match_function_pb2
import app.proto.matchFunction_pb2_grpc as match_function_grpc

from app.services.matchFunction import AsyncMatchFunctionService


DEFAULT_APP_NAME: str = "app-server"
DEFAULT_APP_HOSTNAME: str = "localhost"
DEFAULT_APP_PORT: int = 6565

DEFAULT_AB_BASE_URL: str = "https://demo.accelbyte.io"
DEFAULT_AB_NAMESPACE: str = "accelbyte"
DEFAULT_AB_RESOURCE_NAME: str = "MMV2GRPCSERVICE"

DEFAULT_LOKI_URL: str = "http://localhost:3100/loki/api/v1/push"
DEFAULT_LOKI_USERNAME: str = ""
DEFAULT_LOKI_PASSWORD: str = ""

DEFAULT_PROMETHEUS_ADDR: str = "0.0.0.0"
DEFAULT_PROMETHEUS_PORT: int = 8080
DEFAULT_PROMETHEUS_ENDPOINT: str = "/metrics"


async def main(
    *,
    port: int,
    enable_health_checking: bool = False,
    enable_reflection: bool = False,
    logger: Optional[Logger] = None,
    **kwargs,
) -> None:
    logger = logger if logger is not None else app.logger.DEFAULT_LOGGER

    enable_loki = arg2bool(os.environ.get("ENABLE_LOKI"), default=True)
    enable_log2stderr = arg2bool(os.environ.get("ENABLE_LOG2STDERR"), default=False)
    enable_prometheus = arg2bool(os.environ.get("ENABLE_PROMETHEUS"), default=True)
    enable_zipkin = arg2bool(os.environ.get("ENABLE_ZIPKIN"), default=True)

    enable_interceptor_auth = arg2bool(
        os.environ.get("ENABLE_INTERCEPTOR_AUTH"), default=True
    )
    enable_interceptor_logging = arg2bool(
        os.environ.get("ENABLE_INTERCEPTOR_LOGGING"), default=True
    )
    enable_interceptor_metrics = arg2bool(
        os.environ.get("ENABLE_INTERCEPTOR_METRICS"), default=True
    )

    # otel
    #   uses `APP_NAME`
    service_name = os.environ.get("APP_NAME", DEFAULT_APP_NAME)
    otel_resource = Resource(attributes={SERVICE_NAME: service_name})
    otel_metric_readers = []
    otel_tracer_provider = TracerProvider(resource=otel_resource)
    trace.set_tracer_provider(tracer_provider=otel_tracer_provider)

    if enable_loki:
        # loki
        #   uses `LOKI_URL`, `LOKI_USERNAME`, `LOKI_PASSWORD`
        import logging_loki

        loki_url = os.environ.get("LOKI_URL", DEFAULT_LOKI_URL)
        loki_username = os.environ.get("LOKI_USERNAME", DEFAULT_LOKI_USERNAME)
        loki_password = os.environ.get("LOKI_PASSWORD", DEFAULT_LOKI_PASSWORD)
        loki_auth = (loki_username, loki_password) if loki_username else None
        loki_handler = logging_loki.LokiHandler(
            url=loki_url, auth=loki_auth, version="1"
        )
        logger.addHandler(loki_handler)
        logger.info(f"loki enabled: {loki_url} ({loki_username}:****)")

    if enable_log2stderr:
        logger.addHandler(logging.StreamHandler())
        logger.info("stderr enabled")

    if enable_prometheus:
        # prometheus
        #   uses 'PROMETHEUS_ADDR', 'PROMETHEUS_PORT', 'PROMETHEUS_ENDPOINT', 'PROMETHEUS_PREFIX'
        import threading
        from flask import Flask
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
        from prometheus_client import start_http_server, make_wsgi_app
        from werkzeug.middleware.dispatcher import DispatcherMiddleware

        prometheus_addr = os.environ.get("PROMETHEUS_ADDR", DEFAULT_PROMETHEUS_ADDR)
        prometheus_port = int(
            arg2number(
                os.environ.get("PROMETHEUS_PORT"), default=DEFAULT_PROMETHEUS_PORT
            )
        )
        prometheus_endpoint = os.environ.get(
            "PROMETHEUS_ENDPOINT", DEFAULT_PROMETHEUS_ENDPOINT
        )
        prometheus_prefix = to_camelcase(
            os.environ.get("PROMETHEUS_PREFIX", service_name)
        )
        flask_app = Flask(service_name)
        flask_app.wsgi_app = DispatcherMiddleware(
            app=flask_app.wsgi_app, mounts={prometheus_endpoint: make_wsgi_app()}
        )

        logger.info(
            f"prometheus (flask) http server starting ({prometheus_addr}:{prometheus_port}{prometheus_endpoint})"
        )
        threading.Thread(
            target=lambda: flask_app.run(
                host=prometheus_addr,
                port=prometheus_port,
                debug=True,
                use_reloader=False,
            )
        ).start()

        otel_metric_readers.append(PrometheusMetricReader(prefix=prometheus_prefix))

    if enable_zipkin:
        # zipkin
        #   uses `OTEL_EXPORTER_ZIPKIN_ENDPOINT`, `OTEL_EXPORTER_ZIPKIN_TIMEOUT`
        from opentelemetry.exporter.zipkin.proto.http import ZipkinExporter

        zipkin_endpoint = os.environ.get("OTEL_EXPORTER_ZIPKIN_ENDPOINT")
        trace.get_tracer_provider().add_span_processor(
            span_processor=BatchSpanProcessor(
                span_exporter=ZipkinExporter(
                    endpoint=zipkin_endpoint,
                )
            )
        )
        logger.info(f"zipkin enabled: {zipkin_endpoint}")

    if otel_metric_readers:
        otel_meter_provider = MeterProvider(
            resource=otel_resource, metric_readers=otel_metric_readers
        )
        metrics.set_meter_provider(meter_provider=otel_meter_provider)
        if enable_prometheus:
            logger.info(f"prometheus enabled")

    interceptors = [
        # opentelemetry aio server interceptor
        aio_server_interceptor(),
    ]

    if enable_interceptor_auth:
        # authorization server interceptor
        #   uses `AB_BASE_URL`, `AB_CLIENT_SECRET`, `AB_CLIENT_SECRET`, `AB_NAMESPACE`, `AB_RESOURCE_NAME`, `TOKEN_VALIDATOR_FETCH_INTERVAL`
        from accelbyte_py_sdk import AccelByteSDK
        from accelbyte_py_sdk.core import MyConfigRepository, InMemoryTokenRepository
        from accelbyte_py_sdk.token_validation.caching import CachingTokenValidator
        from app.interceptors.authorization import AuthorizationServerInterceptor

        ab_base_url = os.environ.get("AB_BASE_URL", DEFAULT_AB_BASE_URL)
        ab_client_id = os.environ.get("AB_CLIENT_ID", None)
        ab_client_secret = os.environ.get("AB_CLIENT_SECRET", None)
        ab_namespace = get_env_var(
            key=["AB_NAMESPACE", "NAMESPACE"], default="accelbyte"
        )
        ab_resource_name = os.environ.get("AB_RESOURCE_NAME", DEFAULT_AB_RESOURCE_NAME)
        accelbyte_sdk = AccelByteSDK()
        accelbyte_sdk.initialize(
            options={
                "config": MyConfigRepository(
                    base_url=ab_base_url,
                    client_id=ab_client_id,
                    client_secret=ab_client_secret,
                    namespace=ab_namespace,
                ),
                "token": InMemoryTokenRepository(),
            }
        )
        logger.info(
            f"accelbyte initialized (base_url: {ab_base_url} client_id: {ab_client_id} namespace: {ab_namespace} resource_name: {ab_resource_name})"
        )

        token_validator_fetch_interval = arg2number(
            os.environ.get("TOKEN_VALIDATOR_FETCH_INTERVAL"), default=3600
        )
        token_validator = CachingTokenValidator(
            sdk=accelbyte_sdk,
            token_refresh_interval=token_validator_fetch_interval,
            revocation_list_refresh_interval=token_validator_fetch_interval,
        )
        logger.info("token validator initialized")

        if os.environ.get("PLUGIN_GRPC_SERVER_AUTH_ENABLED") == "true":
            interceptors.append(
                AuthorizationServerInterceptor(
                    resource=f"NAMESPACE:{ab_namespace}:{ab_resource_name}",
                    action=2,
                    namespace=ab_namespace,
                    token_validator=token_validator,
                )
            )

    if enable_interceptor_metrics:
        import platform
        from app.interceptors.metrics import MetricsServerInterceptor

        metrics_labels = {
            "os": platform.system().lower(),
        }
        interceptors.append(MetricsServerInterceptor(labels=metrics_labels))

    if enable_interceptor_logging:
        # debug logging server interceptor
        from app.interceptors.logging import DebugLoggingServerInterceptor

        interceptors.append(DebugLoggingServerInterceptor(logger=logger))

    logger.info(
        "interceptors instantiated:\n- "
        + "\n- ".join([i.__class__.__name__ for i in interceptors])
    )

    server = grpc.aio.server(
        interceptors=interceptors,
    )
    server.add_insecure_port(f"[::]:{port}")

    service = AsyncMatchFunctionService(logger=logger)
    match_function_grpc.add_MatchFunctionServicer_to_server(service, server)

    if enable_health_checking:
        from grpc_health.v1 import health
        from grpc_health.v1 import health_pb2_grpc

        health_pb2_grpc.add_HealthServicer_to_server(
            health.aio.HealthServicer(), server
        )
        logger.info("health checking enabled")

    if enable_reflection:
        from grpc_reflection.v1alpha import reflection

        service_names = [reflection.SERVICE_NAME]

        if enable_health_checking:
            from grpc_health.v1 import health_pb2

            service_names.append(
                health_pb2.DESCRIPTOR.services_by_name["Health"].full_name
            )

        service_names.append(
            match_function_pb2.DESCRIPTOR.services_by_name["MatchFunction"].full_name
        )

        reflection.enable_server_reflection(service_names, server)
        logger.info("reflection enabled")

    logger.info("grpc server starting")
    await server.start()
    logger.info("grpc server started")
    await server.wait_for_termination()


def arg2bool(arg: Any, default: bool = False) -> bool:
    if arg is None:
        return default
    if isinstance(arg, bool):
        return arg
    elif isinstance(arg, (float, int)):
        return arg != 0
    elif isinstance(arg, str):
        return arg.lower() in ("1", "true", "y", "yes")
    elif isinstance(arg, (dict, list)):
        return len(arg) > 0
    else:
        raise NotImplementedError()


def arg2number(arg: Any, default: float = 0) -> float:
    if arg is None:
        return default
    elif isinstance(arg, (float, int)):
        return arg
    elif isinstance(arg, str):
        try:
            return float(arg)
        except ValueError:
            return default
    elif isinstance(arg, (dict, list)):
        return len(arg)
    else:
        raise NotImplementedError()


def get_env_var(key: Union[str, List[str]], default: Optional[str] = None) -> str:
    if isinstance(key, str):
        return os.environ.get(key, default=default)
    elif isinstance(key, list):
        for k in key:
            v = os.environ.get(k, None)
            if v is not None and v != "" and not v.isspace():
                return v
        return default


def to_camelcase(s: str) -> str:
    return s.replace(" ", "_").replace("-", "_").replace(".", "_").strip()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "-n",
        "--host",
        default=DEFAULT_APP_HOSTNAME,
        type=str,
        required=False,
        help="Host[n]ame",
    )

    parser.add_argument(
        "-p",
        "--port",
        default=DEFAULT_APP_PORT,
        type=int,
        required=False,
        help="[P]ort",
    )

    parser.add_argument(
        "-c",
        "--enable_health_checking",
        action="store_true",
        required=False,
        help="Enable Server Health [C]hecking",
    )

    parser.add_argument(
        "-r",
        "--enable_reflection",
        action="store_true",
        required=False,
        help="Enable Server [R]eflection",
    )

    result = vars(parser.parse_args())

    return result


if __name__ == "__main__":
    asyncio.run(main(**parse_args()))
