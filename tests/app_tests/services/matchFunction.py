import asyncio
import json
import unittest
import uuid

from typing import Any, Optional

import grpc

from accelbyte_py_sdk.token_validation.caching import CachingTokenValidator

from app.proto.matchFunction_pb2 import GetStatCodesRequest, StatCodesResponse
from app.proto.matchFunction_pb2 import ValidateTicketRequest, ValidateTicketResponse
from app.proto.matchFunction_pb2 import MakeMatchesRequest, MatchResponse
from app.proto.matchFunction_pb2_grpc import MatchFunctionStub
from app.proto.matchFunction_pb2_grpc import add_MatchFunctionServicer_to_server

from app.interceptors.authorization import AuthorizationServerInterceptor
from app.services.matchFunction import AsyncMatchFunctionService
from app.utils import aiterize

import app_tests.logger


class AsyncMatchFunctionServiceTestCase(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def create_access_token_credentials(access_token):
        return grpc.composite_channel_credentials(
            grpc.local_channel_credentials(),
            grpc.access_token_call_credentials(access_token),
        )

    @staticmethod
    def create_server(
        insecure_port,
        interceptors,
    ):
        server = grpc.aio.server(interceptors=interceptors)
        server.add_insecure_port(insecure_port)
        return server

    async def asyncSetUp(self) -> None:
        self.service = AsyncMatchFunctionService(logger=app_tests.logger.LOGGER)

    async def test_get_stat_codes_returns_stat_codes_response(self):
        # arrange
        request = GetStatCodesRequest()
        request.rules.json = json.dumps(
            {
                "foo": "bar"
            }
        )

        # act
        response = await self.service.GetStatCodes(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, StatCodesResponse)

    async def test_validate_ticket_returns_validate_ticket_response(self):
        # arrange
        request = ValidateTicketRequest()
        request.ticket.ticket_id = "foo"
        request.ticket.match_pool = "foo"
        request.ticket.CreatedAt.GetCurrentTime()
        player = request.ticket.players.add()
        player.player_id = "foo"
        player.attributes["bar"] = "bar"
        request.ticket.ticket_attributes["foo"] = "foo"
        request.ticket.latencies["foo"] = 0
        request.ticket.party_session_id = "foo"
        request.ticket.namespace = "foo"
        request.rules.json = json.dumps({})

        # act
        response = await self.service.ValidateTicket(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, ValidateTicketResponse)

    async def test_make_matches_accepts_make_matches_parameters(self):
        # arrange
        request = self.create_make_matches_request_parameters({})

        # act
        async for _ in self.service.MakeMatches(aiterize([request]), None):
            # assert
            self.fail(msg="match created with not enough players")

    async def test_make_matches_ignores_invalid_make_matches_parameters(self):
        # arrange
        request = MakeMatchesRequest()

        # act
        with self.assertRaises(grpc.aio.AioRpcError):
            async for _ in self.service.MakeMatches(aiterize([request]), None):
                # assert
                self.fail(msg="match function service accepted message without 'parameters' set")

    async def test_make_matches_returns_match_response(self):
        # arrange
        request_parameters = self.create_make_matches_request_parameters({})

        request_ticket1 = self.create_single_player_make_matches_request_ticket()
        request_ticket2 = self.create_single_player_make_matches_request_ticket()

        requests = [
            request_parameters,
            request_ticket1,
            request_ticket2,
        ]

        # act
        responses = []
        async for response in self.service.MakeMatches(aiterize(requests), None):
            responses.append(response)
            # assert
            self.assertIsNotNone(response)
            self.assertIsInstance(response, MatchResponse)

        # assert
        if not responses:
            self.fail(msg="no match created")
        if len(responses) > 1:
            self.fail(msg="created too many matches")

    async def test_authorization_server_interceptor(self):
        import accelbyte_py_sdk.services.auth as auth_service
        from accelbyte_py_sdk import AccelByteSDK
        from accelbyte_py_sdk.core import EnvironmentConfigRepository
        from accelbyte_py_sdk.core import InMemoryTokenRepository
        from accelbyte_py_sdk.core import get_env_user_credentials

        # arrange
        sdk = AccelByteSDK()
        sdk.initialize(
            options={
                "config": EnvironmentConfigRepository(),
                "token": InMemoryTokenRepository(),
            }
        )

        username, password = get_env_user_credentials()
        namespace, error = sdk.get_namespace()
        if error:
            self.fail(msg="can't find namespace")

        result, error = await auth_service.login_user_async(username, password, sdk=sdk)
        access_token = result.access_token

        token_validator = CachingTokenValidator(sdk=sdk)
        interceptor = AuthorizationServerInterceptor(
            resource=f"NAMESPACE:{namespace}:MATCHMAKING",
            action=2,
            namespace=namespace,
            token_validator=token_validator,
        )
        server = self.create_server("[::]:50051", (interceptor,))
        add_MatchFunctionServicer_to_server(self.service, server)

        await server.start()

        try:
            async with grpc.aio.secure_channel(
                "localhost:50051",
                self.create_access_token_credentials(access_token),
            ) as channel:
                stub = MatchFunctionStub(channel)

                # act
                await asyncio.sleep(10)
                response = await stub.GetStatCodes(GetStatCodesRequest())

                # assert
                self.assertIsNotNone(response)
                self.assertIsInstance(response, StatCodesResponse)
        finally:
            await server.stop(grace=None)

    @staticmethod
    def create_make_matches_request_parameters(
        rule_obj: Any,
        scope_ab_trace_id: str = "foo",
    ):
        result = MakeMatchesRequest()
        result.parameters.scope.ab_trace_id = scope_ab_trace_id
        result.parameters.rules.json = json.dumps(rule_obj)
        return result

    @staticmethod
    def create_single_player_make_matches_request_ticket(
        ticket_id: Optional[str] = None, player_id: Optional[str] = None
    ):
        if ticket_id is None:
            ticket_id = uuid.uuid4().__str__()
        if player_id is None:
            player_id = uuid.uuid4().__str__()
        result = MakeMatchesRequest()
        result.ticket.ticket_id = ticket_id
        result.ticket.CreatedAt.GetCurrentTime()
        result.ticket.players.add().player_id = player_id
        return result
