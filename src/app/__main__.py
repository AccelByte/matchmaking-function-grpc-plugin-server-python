import concurrent.futures
import logging

from typing import Optional

import grpc

import app.proto.matchFunction_pb2 as match_func_proto
import app.proto.matchFunction_pb2_grpc as match_func_grpc

import app.interceptor
import app.logger
import app.servicer


def main(max_workers: int = 10, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    logger = logger if logger is not None else app.logger.DEFAULT_LOGGER

    interceptors = (
        app.interceptor.AuthorizationInterceptor(),
        app.interceptor.DebugLoggerInterceptor(),
        app.interceptor.ExceptionHandlingInterceptor(),
    )
    server = grpc.server(
        concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
        ),
        interceptors=interceptors,
    )

    servicer = app.servicer.MatchFunctionServicer()
    match_func_grpc.add_MatchFunctionServicer_to_server(servicer, server)

    server.add_insecure_port("[::]:50051")
    server.start()
    logger.info("server has started")

    server.wait_for_termination()


if __name__ == "__main__":
    main()
