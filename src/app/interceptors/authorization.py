from logging import Logger
from typing import Any, Awaitable, Callable, Coroutine, Optional

import grpc
import grpc.aio

import accelbyte_py_sdk.api.iam as iam_service
from accelbyte_py_sdk import AccelByteSDK


BEARER_PREFIX: str = "Bearer "


class AuthorizationServerInterceptor(grpc.aio.ServerInterceptor):

    def __init__(self, namespace: str, resource_name: str, sdk: AccelByteSDK, logger: Optional[Logger] = None):
        self.namespace = namespace
        self.required_permission = "NAMESPACE:{namespace}:{resource_name}".format(namespace=namespace, resource_name=resource_name)
        self.sdk = sdk
        self.logger = logger

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        if (authorization := next(
            (
                metadata.value
                for metadata in handler_call_details.invocation_metadata
                if metadata.key == "authorization"
            ),
            None,
        )) and authorization is None:
            raise self.create_unauthenticated_error(error="no authorization token found")

        if not authorization.startswith(BEARER_PREFIX):
            raise self.create_unauthenticated_error(error="invalid authorization token format")

        access_token = authorization.removeprefix(BEARER_PREFIX)

        result, error = await iam_service.verify_token_v3_async(token=access_token, sdk=self.sdk)
        if error:
            raise self.create_unauthenticated_error(error="invalid authorization token value: {error}".format(error=error))

        if not result.permissions:
            raise self.create_unauthenticated_error(error="unauthorized call")

        if next((permission for permission in result.permissions if permission.resource == self.required_permission), None) is None:
            raise self.create_unauthenticated_error(error="unauthorized call")

        return await continuation(handler_call_details)

    @staticmethod
    def create_unauthenticated_error(error: str):
        return grpc.aio.AioRpcError(grpc.StatusCode.UNAUTHENTICATED, None, None, details=error, debug_error_string=error)
