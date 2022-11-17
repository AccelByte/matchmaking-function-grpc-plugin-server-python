from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional

import grpc.aio

from prometheus_client import Counter


class MetricsServerInterceptor(grpc.aio.ServerInterceptor):
    def __init__(
        self,
        meter_name: str = "com.accelbyte.app",
        meter_version: str = "1.0.0",
        labels: Optional[Dict[str, Any]] = None,
    ):
        self.meter_name = meter_name
        self.meter_version = meter_version
        self.labels = labels

        counter_name = "grpc_server_calls"
        counter_unit = "count"
        counter_description = "number of GRPC calls"

        self.counter = Counter(
            name=counter_name,
            documentation=counter_description,
            labelnames=labels.keys(),
            unit=counter_unit,
        )

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        self.counter.labels(**self.labels).inc(amount=1)
        return await continuation(handler_call_details)
