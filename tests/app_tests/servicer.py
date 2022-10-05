import json
import unittest

import google.protobuf.struct_pb2 as struct_proto
import google.protobuf.timestamp_pb2 as timestamp_proto

import app.proto.matchFunction_pb2_grpc as match_func_grpc
import app.proto.matchFunction_pb2 as match_func_proto

import app.servicer


class MatchFunctionServicerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.servicer = app.servicer.MatchFunctionServicer()

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

    def test_make_matches_returns_match_response(self):
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
        requests = [
            match_func_proto.MakeMatchesRequest(
                parameters=match_func_proto.MakeMatchesRequest.MakeMatchesParameters(
                    scope=match_func_proto.Scope(
                        ab_trace_id="foo",
                    ),
                    rules=match_func_proto.Rules(json=json.dumps({})),
                )
            ),
            match_func_proto.MakeMatchesRequest(
                ticket=match_func_proto.Ticket(
                    ticket_id="foo",
                    match_pool="foo",
                    CreatedAt=created_at,
                    players=players,
                    ticket_attributes=ticket_attributes,
                    latencies={
                        "foo": 0,
                    },
                )
            ),
        ]

        # act
        for response in self.servicer.MakeMatches(requests, None):
            # assert
            self.assertIsNotNone(response)
            self.assertIsInstance(response, match_func_proto.MatchResponse)
