import asyncio
import logging
import os

from typing import Any

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

DEFAULT_AB_BASE_URL: str = "https://test.accelbyte.io"
DEFAULT_AB_NAMESPACE: str = "accelbyte"

DEFAULT_PROMETHEUS_ADDR: str = "0.0.0.0"
DEFAULT_PROMETHEUS_PORT: int = 8080
DEFAULT_PROMETHEUS_ENDPOINT: str = "/metrics"


async def main(**kwargs) -> None:
    logger = app.logger.DEFAULT_LOGGER

    port = int(arg2number(os.environ.get("PORT"), default=DEFAULT_APP_PORT))
    enable_health_checking = arg2bool(os.environ.get("ENABLE_HEALTH_CHECKING"), default=True)
    enable_log2stderr = arg2bool(os.environ.get("ENABLE_LOG2STDERR"), default=False)
    enable_prometheus = arg2bool(os.environ.get("ENABLE_PROMETHEUS"), default=True)
    enable_reflection = arg2bool(os.environ.get("ENABLE_REFLECTION"), default=True)
    enable_zipkin = arg2bool(os.environ.get("ENABLE_ZIPKIN"), default=True)

    enable_interceptor_auth = arg2bool(
        os.environ.get("PLUGIN_GRPC_SERVER_AUTH_ENABLED"), default=True
    )
    enable_interceptor_logging = arg2bool(
        os.environ.get("ENABLE_INTERCEPTOR_LOGGING"), default=False
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
        #   uses `AB_BASE_URL`, `AB_CLIENT_SECRET`, `AB_CLIENT_SECRET`, `AB_NAMESPACE`, `TOKEN_VALIDATOR_FETCH_INTERVAL`
        from accelbyte_py_sdk import AccelByteSDK
        from accelbyte_py_sdk.core import MyConfigRepository, InMemoryTokenRepository
        from accelbyte_py_sdk.token_validation.caching import CachingTokenValidator
        from accelbyte_py_sdk.services.auth import login_client, LoginClientTimer
        from app.interceptors.authorization import AuthorizationServerInterceptor

        ab_base_url = os.environ.get("AB_BASE_URL", DEFAULT_AB_BASE_URL)
        ab_client_id = os.environ.get("AB_CLIENT_ID", None)
        ab_client_secret = os.environ.get("AB_CLIENT_SECRET", None)
        ab_namespace = os.environ.get("AB_NAMESPACE", DEFAULT_AB_NAMESPACE)

        config = MyConfigRepository(ab_base_url, ab_client_id, ab_client_secret, ab_namespace)
        token = InMemoryTokenRepository()
        sdk = AccelByteSDK()
        sdk.initialize(options={"config": config, "token": token})
        logger.info(
            f"accelbyte initialized (base_url: {ab_base_url} client_id: {ab_client_id} namespace: {ab_namespace})"
        )
        result, error = login_client(sdk=sdk)
        if error:
            raise Exception(str(error))

        sdk.timer = LoginClientTimer(2880, repeats=-1, autostart=True, sdk=sdk)

        token_validator_fetch_interval = arg2number(
            os.environ.get("TOKEN_VALIDATOR_FETCH_INTERVAL"), default=3600
        )
        token_validator = CachingTokenValidator(
            sdk=sdk,
            token_refresh_interval=token_validator_fetch_interval,
            revocation_list_refresh_interval=token_validator_fetch_interval,
        )
        logger.info("token validator initialized")

        interceptors.append(
            AuthorizationServerInterceptor(
                token_validator=token_validator,
                namespace=ab_namespace,
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
    

def to_camelcase(s: str) -> str:
    return s.replace(" ", "_").replace("-", "_").replace(".", "_").strip()


if __name__ == "__main__":
    asyncio.run(main())
