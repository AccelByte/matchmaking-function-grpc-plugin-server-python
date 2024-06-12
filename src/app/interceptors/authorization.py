from typing import Awaitable, Callable, List

from grpc import HandlerCallDetails, RpcMethodHandler, StatusCode
from grpc.aio import AioRpcError, Metadata, ServerInterceptor

from accelbyte_py_sdk.services.auth import parse_access_token
from accelbyte_py_sdk.token_validation import TokenValidatorProtocol


class AuthorizationServerInterceptor(ServerInterceptor):
    whitelisted_methods: List[str] = [
        "/grpc.health.v1.Health/Check",
        "/grpc.health.v1.Health/Watch",
        "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
    ]

    def __init__(
        self,
        namespace: str,
        token_validator: TokenValidatorProtocol,
    ):
        self.namespace = namespace
        self.token_validator = token_validator

    async def intercept_service(
        self,
        continuation: Callable[[HandlerCallDetails], Awaitable[RpcMethodHandler]],
        handler_call_details: HandlerCallDetails,
    ) -> RpcMethodHandler:
        method = getattr(handler_call_details, "method", "")
        if method in self.whitelisted_methods:
            return await continuation(handler_call_details)

        authorization = next(
            (
                metadata.value
                for metadata in handler_call_details.invocation_metadata
                if metadata.key == "authorization"
            ),
            None,
        )

        if authorization is None:
            raise self.create_aio_rpc_error(error="no authorization token found")

        if not authorization.startswith("Bearer "):
            raise self.create_aio_rpc_error(error="invalid authorization token format")

        try:
            token = authorization.removeprefix("Bearer ")
            error = self.token_validator.validate_token(
                token=token,
                namespace=self.namespace
            )
            if error is not None:
                raise error
            claims, error = parse_access_token(token)
            if error is not None:
                raise error
            if extend_namespace := claims.get("extend_namespace", None):
                if extend_namespace != self.namespace:
                    raise self.create_aio_rpc_error(
                        error=f"'{extend_namespace}' does not match '{self.namespace}'",
                        code=StatusCode.PERMISSION_DENIED,
                    )
        except AioRpcError as rpc_error:
            raise rpc_error
        except Exception as e:
            raise self.create_aio_rpc_error(
                error=str(e), code=StatusCode.INTERNAL
            ) from e

        return await continuation(handler_call_details)

    @staticmethod
    def create_aio_rpc_error(
        error: str, code: StatusCode = StatusCode.UNAUTHENTICATED
    ) -> AioRpcError:
        return AioRpcError(
            code=code,
            initial_metadata=Metadata(),
            trailing_metadata=Metadata(),
            details=error,
            debug_error_string=error,
        )
