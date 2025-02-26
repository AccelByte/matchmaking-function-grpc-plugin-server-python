from logging import Logger
from typing import Iterable, Optional

from accelbyte_py_sdk import AccelByteSDK
from accelbyte_py_sdk.core import HttpxHttpClient, RequestsHttpClient


async def aiterize(iterable: Iterable):
    for item in iterable:
        yield item


def instrument_sdk_http_client(sdk: AccelByteSDK, logger: Optional[Logger] = None) -> None:
    http_client = sdk.get_http_client(raise_when_none=False)
    if http_client is not None:
        if isinstance(http_client, HttpxHttpClient):
            try:
                from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
                HTTPXClientInstrumentor().instrument()
                if logger:
                    logger.info("httpx client instrumented")
            except ImportError:
                if logger:
                    logger.warning("failed to instrument httpx client")
        elif isinstance(http_client, RequestsHttpClient):
            try:
                from opentelemetry.instrumentation.requests import RequestsInstrumentor
                RequestsInstrumentor().instrument()
                if logger:
                    logger.info("requests client instrumented")
            except ImportError:
                if logger:
                    logger.warning("failed to instrument requests client")
        else:
            if logger:
                logger.warning("failed to instrument unknown client")
