import json
import logging
import unittest
import uuid

from typing import Optional

import google.protobuf.struct_pb2 as struct_proto
import google.protobuf.timestamp_pb2 as timestamp_proto

import app.proto.matchFunction_pb2_grpc as match_func_grpc
import app.proto.matchFunction_pb2 as match_func_proto

import app.ctypes
import app.servicer

import app_tests.logger


class MatchFunctionServicerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.servicer = app.servicer.MatchFunctionServicer(
            logger=app_tests.logger.LOGGER,
        )

    def test_get_stat_codes_returns_stat_codes_response(self):
        # arrange
        request = match_func_proto.GetStatCodesRequest(
            rules=match_func_proto.Rules(json=json.dumps({}))
        )

        # act
        response = self.servicer.GetStatCodes(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, match_func_proto.StatCodesResponse)

    def test_validate_ticket_returns_validate_ticket_response(self):
        # arrange
        created_at = timestamp_proto.Timestamp()
        created_at.GetCurrentTime()
        player_attributes = struct_proto.Struct()
        player_attributes.update(
            {
                "bar": "bar",
            }
        )
        players = [
            match_func_proto.Ticket.PlayerData(
                player_id="foo",
                attributes=player_attributes,
            )
        ]
        ticket_attributes = struct_proto.Struct()
        ticket_attributes.update(
            {
                "foo": "foo",
            }
        )
        request = match_func_proto.ValidateTicketRequest(
            ticket=match_func_proto.Ticket(
                ticket_id="foo",
                match_pool="foo",
                CreatedAt=created_at,
                players=players,
                ticket_attributes=ticket_attributes,
                latencies={
                    "foo": 0,
                },
            ),
            rules=match_func_proto.Rules(json=json.dumps({})),
        )

        # act
        response = self.servicer.ValidateTicket(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, match_func_proto.ValidateTicketResponse)

    def test_make_matches_accepts_make_matches_parameters(self):
        # arrange
        rules_ship_count_min, rules_ship_count_max = 1, 10
        request = self.create_make_matches_request_parameters(
            rules_ship_count_min=rules_ship_count_min,
            rules_ship_count_max=rules_ship_count_max,
        )

        # act
        for response in self.servicer.MakeMatches([request], None):
            self.fail(msg="match created with not enough players")
        else:
            # assert
            self.assertEqual(rules_ship_count_min, self.servicer.ship_count_min)
            self.assertEqual(rules_ship_count_max, self.servicer.ship_count_max)

    def test_make_matches_ignores_invalid_make_matches_parameters(self):
        # arrange
        current_ship_count_min = self.servicer.ship_count_min
        current_ship_count_max = self.servicer.ship_count_max
        request = self.create_make_matches_request_parameters(
            rules_ship_count_min=0,
            rules_ship_count_max=0,
        )  # invalid: min && max must be non-zero

        # act
        for response in self.servicer.MakeMatches([request], None):
            self.fail(msg="match created with not enough players")
        else:
            # assert
            self.assertEqual(current_ship_count_min, self.servicer.ship_count_min)
            self.assertEqual(current_ship_count_max, self.servicer.ship_count_max)

    def test_make_matches_returns_match_response(self):
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
        for response in self.servicer.MakeMatches(requests, None):
            responses.append(response)

            # assert
            self.assertIsNotNone(response)
            self.assertIsInstance(response, match_func_proto.MatchResponse)

        # assert
        if not responses:
            self.fail(msg="no match created")
        if len(responses) > 1:
            self.fail(msg="created too many matches")

    @staticmethod
    def create_make_matches_request_parameters(
        rules_ship_count_min: int,
        rules_ship_count_max: int,
        scope_ab_trace_id: str = "foo",
    ):
        rule_obj = app.ctypes.RuleObject(
            shipCountMin=rules_ship_count_min, shipCountMax=rules_ship_count_max
        )
        rule_json = json.dumps(rule_obj.__dict__)
        return match_func_proto.MakeMatchesRequest(
            parameters=match_func_proto.MakeMatchesRequest.MakeMatchesParameters(
                scope=match_func_proto.Scope(
                    ab_trace_id=scope_ab_trace_id,
                ),
                rules=match_func_proto.Rules(json=rule_json),
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
        created_at = timestamp_proto.Timestamp()
        created_at.GetCurrentTime()
        return match_func_proto.MakeMatchesRequest(
            ticket=match_func_proto.Ticket(
                ticket_id=ticket_id,
                CreatedAt=created_at,
                players=[
                    match_func_proto.Ticket.PlayerData(
                        player_id=player_id,
                    )
                ],
            )
        )
