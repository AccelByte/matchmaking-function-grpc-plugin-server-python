from logging import Logger
from typing import Optional

import grpc
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
            self.logger.info(handler_call_details)
        return await continuation(handler_call_details)
