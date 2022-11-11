from logging import Logger
from typing import Awaitable, Callable, Optional

import grpc.aio


class DebugLoggingServerInterceptor(grpc.aio.ServerInterceptor):
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        if self.logger:
            self.logger.info(f"method: {handler_call_details.method}")
        return await continuation(handler_call_details)
