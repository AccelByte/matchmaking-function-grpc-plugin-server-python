import json

from typing import List

import google.protobuf.struct_pb2 as struct_proto
import google.protobuf.timestamp_pb2 as timestamp_proto

import app.proto.matchFunction_pb2_grpc as match_func_grpc
import app.proto.matchFunction_pb2 as match_func_proto


class MatchFunctionServicer(match_func_grpc.MatchFunctionServicer):
    def __init__(self, ship_count_min: int = 2, ship_count_max: int = 2):
        self.ship_count_min: int = ship_count_min
        self.ship_count_max: int = ship_count_max

        self.unmatched_tickets: List[match_func_proto.Ticket] = []

    def GetStatCodes(self, request, context):
        return match_func_proto.StatCodesResponse(codes=["foo", "bar"])

    def ValidateTicket(self, request, context):
        return match_func_proto.ValidateTicketResponse(valid=True)

    def MakeMatches(self, request_iterator, context):
        for request in request_iterator:
            if request.HasField("parameters"):
                parameters = request.parameters
                rules = parameters.rules
                json_str = rules.json
                parameters_json = json.loads(json_str)
                new_ship_count_min = parameters_json.get("shipCountMin")
                new_ship_count_max = parameters_json.get("shipCountMax")
                if (
                    new_ship_count_min is not None
                    and new_ship_count_max is not None
                    and new_ship_count_min != 0
                    and new_ship_count_max != 0
                    and new_ship_count_min <= new_ship_count_max
                ):
                    self.ship_count_min = new_ship_count_min
                    self.ship_count_max = new_ship_count_max
            elif request.HasField("ticket"):
                ticket = request.ticket
                self.unmatched_tickets.append(ticket)
                if len(self.unmatched_tickets) == self.ship_count_max:
                    match_response = self.__make_match_response_from_tickets(
                        self.unmatched_tickets
                    )
                    self.unmatched_tickets.clear()
                    yield match_response

    @staticmethod
    def __make_match_response_from_tickets(tickets: List[match_func_proto.Ticket]):
        # TODO(elmer): allow only unique IDs (?)
        player_ids = [
            player.player_id for ticket in tickets for player in ticket.players
        ]

        return match_func_proto.MatchResponse(
            match=match_func_proto.Match(
                teams=[match_func_proto.Match.Team(user_ids=player_ids)],
                region_preferences=["any"],
            )
        )
