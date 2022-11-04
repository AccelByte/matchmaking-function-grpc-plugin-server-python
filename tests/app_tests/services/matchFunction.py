import asyncio
import json
import unittest
import uuid

from typing import Optional

import grpc

from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from app.proto.matchFunction_pb2 import Match, Rules, Scope, Ticket
from app.proto.matchFunction_pb2 import GetStatCodesRequest, StatCodesResponse
from app.proto.matchFunction_pb2 import ValidateTicketRequest, ValidateTicketResponse
from app.proto.matchFunction_pb2 import MakeMatchesRequest, MatchResponse
from app.proto.matchFunction_pb2_grpc import MatchFunctionStub
from app.proto.matchFunction_pb2_grpc import add_MatchFunctionServicer_to_server

from app.auth.token_validator import TokenValidator
from app.ctypes import RuleObject
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
        rule_obj = RuleObject(shipCountMin=2, shipCountMax=2)
        rule_json = json.dumps(rule_obj.__dict__)
        request = GetStatCodesRequest(
            rules=Rules(
                json=rule_json,
            ),
        )

        # act
        response = await self.service.GetStatCodes(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, StatCodesResponse)

    async def test_validate_ticket_returns_validate_ticket_response(self):
        # arrange
        created_at = Timestamp()
        created_at.GetCurrentTime()
        player_attributes = Struct()
        player_attributes.update(
            {
                "bar": "bar",
            }
        )
        players = [
            Ticket.PlayerData(
                player_id="foo",
                attributes=player_attributes,
            )
        ]
        ticket_attributes = Struct()
        ticket_attributes.update(
            {
                "foo": "foo",
            }
        )
        request = ValidateTicketRequest(
            ticket=Ticket(
                ticket_id="foo",
                match_pool="foo",
                CreatedAt=created_at,
                players=players,
                ticket_attributes=ticket_attributes,
                latencies={
                    "foo": 0,
                },
            ),
            rules=Rules(json=json.dumps({})),
        )

        # act
        response = await self.service.ValidateTicket(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, ValidateTicketResponse)

    async def test_make_matches_accepts_make_matches_parameters(self):
        # arrange
        rules_ship_count_min, rules_ship_count_max = 1, 10
        request = self.create_make_matches_request_parameters(
            rules_ship_count_min=rules_ship_count_min,
            rules_ship_count_max=rules_ship_count_max,
        )
        requests = [request]

        async for response in self.service.MakeMatches(aiterize(requests), None):
            self.fail(msg="match created with not enough players")
        else:
            # assert
            self.assertEqual(rules_ship_count_min, self.service.ship_count_min)
            self.assertEqual(rules_ship_count_max, self.service.ship_count_max)

    async def test_make_matches_ignores_invalid_make_matches_parameters(self):
        # arrange
        request = self.create_make_matches_request_parameters(
            rules_ship_count_min=0,
            rules_ship_count_max=0,
        )  # invalid: min && max must be non-zero
        requests = [request]

        current_ship_count_min = self.service.ship_count_min
        current_ship_count_max = self.service.ship_count_max
        async for response in self.service.MakeMatches(aiterize(requests), None):
            self.fail(msg="match created with not enough players")
        else:
            # assert
            self.assertEqual(current_ship_count_min, self.service.ship_count_min)
            self.assertEqual(current_ship_count_max, self.service.ship_count_max)

    async def test_make_matches_returns_match_response(self):
        # arrange
        requests = [
            self.create_make_matches_request_parameters(
                rules_ship_count_min=2, rules_ship_count_max=2
            ),
            self.create_single_player_make_matches_request_ticket(player_id="player1"),
            self.create_single_player_make_matches_request_ticket(player_id="player2"),
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

        token_validator = TokenValidator(sdk=sdk)
        await token_validator.initialize()

        interceptor = AuthorizationServerInterceptor(
            namespace=namespace,
            resource_name="MATCHMAKING",
            token_validator=token_validator,
            logger=app_tests.logger.LOGGER,
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
        rules_ship_count_min: int,
        rules_ship_count_max: int,
        scope_ab_trace_id: str = "foo",
    ):
        rule_obj = RuleObject(
            shipCountMin=rules_ship_count_min, shipCountMax=rules_ship_count_max
        )
        rule_json = json.dumps(rule_obj.__dict__)
        return MakeMatchesRequest(
            parameters=MakeMatchesRequest.MakeMatchesParameters(
                scope=Scope(
                    ab_trace_id=scope_ab_trace_id,
                ),
                rules=Rules(json=rule_json),
            )
        )

    @staticmethod
    def create_single_player_make_matches_request_ticket(
        ticket_id: Optional[str] = None, player_id: Optional[str] = None
    ):
        if ticket_id is None:
            ticket_id = uuid.uuid4().__str__()
        if player_id is None:
            player_id = uuid.uuid4().__str__()
        created_at = Timestamp()
        created_at.GetCurrentTime()
        return MakeMatchesRequest(
            ticket=Ticket(
                ticket_id=ticket_id,
                CreatedAt=created_at,
                players=[
                    Ticket.PlayerData(
                        player_id=player_id,
                    )
                ],
            )
        )
