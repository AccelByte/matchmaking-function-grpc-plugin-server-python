import asyncio

from argparse import ArgumentParser
from logging import Logger
from typing import Optional

import grpc.aio

import app.logger

import app.proto.matchFunction_pb2 as match_function_pb2
import app.proto.matchFunction_pb2_grpc as match_function_grpc

from app.interceptors.authorization import AuthorizationServerInterceptor
from app.services.matchFunction import AsyncMatchFunctionService


async def main(
    *,
    port: int,
    enable_reflection: bool = False,
    logger: Optional[Logger] = None,
    **kwargs,
) -> None:
    logger = logger if logger is not None else app.logger.DEFAULT_LOGGER

    interceptors = []
    interceptors.append(AuthorizationServerInterceptor())

    server = grpc.aio.server(
        interceptors=tuple(interceptors),
    )
    server.add_insecure_port(f"[::]:{port}")

    service = AsyncMatchFunctionService(logger=logger)
    match_function_grpc.add_MatchFunctionServicer_to_server(service, server)

    if enable_reflection:
        from grpc_reflection.v1alpha import reflection

        SERVICE_NAMES = (
            match_function_pb2.DESCRIPTOR.services_by_name["MatchFunction"].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(SERVICE_NAMES, server)

    await server.start()
    await server.wait_for_termination()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "-n",
        "--host",
        default="127.0.0.1",
        type=str,
        required=False,
        help="Host[n]ame",
    )

    parser.add_argument(
        "-p",
        "--port",
        default=50051,
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
