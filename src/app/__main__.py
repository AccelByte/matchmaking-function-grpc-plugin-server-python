import asyncio
import logging
import os

from argparse import ArgumentParser
from logging import Logger
from typing import Any, List, Optional, Union

import grpc.aio
import logging_loki

from opentelemetry import trace
from opentelemetry.exporter.zipkin.proto.http import ZipkinExporter
from opentelemetry.instrumentation.grpc import aio_server_interceptor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from accelbyte_py_sdk import AccelByteSDK
from accelbyte_py_sdk.core import MyConfigRepository, InMemoryTokenRepository

import app.logger

import app.proto.matchFunction_pb2 as match_function_pb2
import app.proto.matchFunction_pb2_grpc as match_function_grpc

from app.auth.token_validator import TokenValidator
from app.interceptors.authorization import AuthorizationServerInterceptor
from app.interceptors.logging import DebugLoggingServerInterceptor
from app.services.matchFunction import AsyncMatchFunctionService


DEFAULT_APP_NAME: str = "app"
DEFAULT_APP_HOSTNAME: str = "localhost"
DEFAULT_APP_PORT: int = 6565

DEFAULT_AB_BASE_URL: str = "https://demo.accelbyte.io"
DEFAULT_AB_NAMESPACE: str = "accelbyte"
DEFAULT_AB_RESOURCE_NAME: str = "MMV2GRPCSERVICE"

DEFAULT_LOKI_URL: str = "http://localhost:3100/loki/api/v1/push"
DEFAULT_LOKI_USERNAME: str = ""
DEFAULT_LOKI_PASSWORD: str = ""


async def main(
    *,
    port: int,
    enable_reflection: bool = False,
    logger: Optional[Logger] = None,
    **kwargs,
) -> None:
    logger = logger if logger is not None else app.logger.DEFAULT_LOGGER

    # otel
    #   uses `APP_NAME`
    service_name = os.environ.get("APP_NAME", DEFAULT_APP_NAME)
    otel_resource = Resource(attributes={SERVICE_NAME: service_name})
    otel_provider = TracerProvider(resource=otel_resource)
    trace.set_tracer_provider(tracer_provider=otel_provider)

    if arg2bool(os.environ.get("ENABLE_LOKI"), default=True):
        # loki
        #   uses `LOKI_URL`, `LOKI_USERNAME`, `LOKI_PASSWORD`
        loki_url = os.environ.get("LOKI_URL", DEFAULT_LOKI_URL)
        loki_username = os.environ.get("LOKI_USERNAME", DEFAULT_LOKI_USERNAME)
        loki_password = os.environ.get("LOKI_PASSWORD", DEFAULT_LOKI_PASSWORD)
        loki_auth = (loki_username, loki_password)
        loki_handler = logging_loki.LokiHandler(
            url=loki_url, auth=loki_auth, version="1"
        )
        logger.addHandler(loki_handler)
        logger.info(f"loki enabled: {loki_url} ({loki_username}:****)")

    if arg2bool(os.environ.get("ENABLE_LOG2STDERR"), default=False):
        logger.addHandler(logging.StreamHandler())
        logger.info("stderr enabled")

    if arg2bool(os.environ.get("ENABLE_ZIPKIN"), default=True):
        # zipkin
        #   uses `OTEL_EXPORTER_ZIPKIN_ENDPOINT`, `OTEL_EXPORTER_ZIPKIN_TIMEOUT`
        zipkin_endpoint = os.environ.get("OTEL_EXPORTER_ZIPKIN_ENDPOINT")
        trace.get_tracer_provider().add_span_processor(
            span_processor=BatchSpanProcessor(
                span_exporter=ZipkinExporter(
                    endpoint=zipkin_endpoint,
                )
            )
        )
        logger.info(f"zipkin enabled: {zipkin_endpoint}")

    # accelbyte
    #   uses `APP_SECURITY_BASE_URL`, `APP_SECURITY_CLIENT_SECRET`, `APP_SECURITY_CLIENT_SECRET`, `APP_SECURITY_NAMESPACE`
    ab_base_url = os.environ.get("APP_SECURITY_BASE_URL", DEFAULT_AB_BASE_URL)
    ab_client_id = os.environ.get("APP_SECURITY_CLIENT_ID", None)
    ab_client_secret = os.environ.get("APP_SECURITY_CLIENT_SECRET", None)
    ab_namespace = get_env_var(
        key=["APP_SECURITY_NAMESPACE", "NAMESPACE"], default="accelbyte"
    )
    ab_resource_name = os.environ.get(
        "APP_SECURITY_RESOURCE_NAME", DEFAULT_AB_RESOURCE_NAME
    )
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

    interceptors = [
        # opentelemetry aio server interceptor
        aio_server_interceptor(),
    ]

    # authorization server interceptor
    #   uses `APP_SECURITY_NAMESPACE`, `APP_SECURITY_RESOURCE_NAME`, `ENABLE_INTERCEPTOR_AUTH`, `TOKEN_VALIDATOR_FETCH_INTERVAL`
    if arg2bool(os.environ.get("ENABLE_INTERCEPTOR_AUTH"), default=True):
        token_validator_fetch_interval = arg2number(
            os.environ.get("TOKEN_VALIDATOR_FETCH_INTERVAL"), default=3600
        )
        token_validator = TokenValidator(
            sdk=accelbyte_sdk, fetch_interval=token_validator_fetch_interval
        )
        logger.info(
            f"token validator initializing (fetch_interval: {token_validator_fetch_interval}s)"
        )
        await token_validator.initialize()
        logger.info("token validator initialized")

        interceptors.append(
            AuthorizationServerInterceptor(
                namespace=ab_namespace,
                resource_name=ab_resource_name,
                token_validator=token_validator,
                logger=logger,
            )
        )

    # debug logging server interceptor
    #   uses `ENABLE_INTERCEPTOR_DEBUG`
    if arg2bool(os.environ.get("ENABLE_INTERCEPTOR_DEBUG"), default=True):
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

    if enable_reflection:
        from grpc_reflection.v1alpha import reflection

        service_names = (
            match_function_pb2.DESCRIPTOR.services_by_name["MatchFunction"].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)
        logger.info("reflection enabled")

    logger.info("server starting")
    await server.start()
    logger.info("server started")
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
