from logging import Logger
from typing import Awaitable, Callable, Optional

import grpc
import grpc.aio

from app.auth.token_validator import TokenValidator
from app.auth.models import Permission


class AuthorizationServerInterceptor(grpc.aio.ServerInterceptor):
    BEARER_PREFIX: str = "Bearer "

    def __init__(
        self,
        namespace: str,
        resource_name: str,
        token_validator: TokenValidator,
        logger: Optional[Logger] = None,
    ):
        self.namespace: str = namespace
        self.resource_name: str = resource_name
        self.token_validator: TokenValidator = token_validator
        self.logger: Optional[Logger] = logger

        self.required_permission: Permission = Permission.create(
            action=2,
            resource=f"NAMESPACE:{namespace}:{resource_name}",
        )

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        if (
            authorization := next(
                (
                    metadata.value
                    for metadata in handler_call_details.invocation_metadata
                    if metadata.key == "authorization"
                ),
                None,
            )
        ) and authorization is None:
            raise self.create_aio_rpc_error(error="no authorization token found")

        if not authorization.startswith(self.BEARER_PREFIX):
            raise self.create_aio_rpc_error(error="invalid authorization token format")

        try:
            token = authorization.removeprefix(self.BEARER_PREFIX)
            if self.logger:
                self.logger.info(f"validating {token}")
            if not await self.token_validator.validate(
                token=token,
                permission=self.required_permission,
                namespace=self.namespace,
                user_id=None,
            ):
                raise self.create_aio_rpc_error(error="unauthorized call")
        except Exception as e:
            raise self.create_aio_rpc_error(
                error=str(e), status_code=grpc.StatusCode.INTERNAL
            ) from e

        return await continuation(handler_call_details)

    @staticmethod
    def create_aio_rpc_error(
        error: str, status_code: grpc.StatusCode = grpc.StatusCode.UNAUTHENTICATED
    ):
        return grpc.aio.AioRpcError(
            status_code,
            grpc.aio.Metadata(),
            grpc.aio.Metadata(),
            details=error,
            debug_error_string=error,
        )
