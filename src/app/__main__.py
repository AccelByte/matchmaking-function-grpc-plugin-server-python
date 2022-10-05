import concurrent.futures

import grpc

import app.proto.matchFunction_pb2 as match_func_proto
import app.proto.matchFunction_pb2_grpc as match_func_grpc

import app.interceptor
import app.servicer


def main(max_workers: int = 10, **kwargs) -> None:
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
    server.wait_for_termination()


if __name__ == "__main__":
    main()
