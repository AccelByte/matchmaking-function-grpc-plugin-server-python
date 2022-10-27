import json

from logging import Logger, getLogger
from typing import List, Optional

from app.proto.matchFunction_pb2 import Match, Ticket
from app.proto.matchFunction_pb2 import StatCodesResponse
from app.proto.matchFunction_pb2 import ValidateTicketResponse
from app.proto.matchFunction_pb2 import MatchResponse
from app.proto.matchFunction_pb2_grpc import MatchFunctionServicer


def make_match_response_from_tickets(tickets: List[Ticket]):
    # TODO(elmer): allow only unique IDs (?)
    player_ids = [player.player_id for ticket in tickets for player in ticket.players]
    return MatchResponse(
        match=Match(
            teams=[Match.Team(user_ids=player_ids)],
            region_preferences=["any"],
        )
    )


class AsyncMatchFunctionService(MatchFunctionServicer):
    def __init__(
        self,
        ship_count_min: int = 2,
        ship_count_max: int = 2,
        logger: Optional[Logger] = None,
    ):
        self.ship_count_min: int = ship_count_min
        self.ship_count_max: int = ship_count_max

        self.unmatched_tickets: List[Ticket] = []

        self.logger = (
            logger if logger is not None else getLogger(self.__class__.__name__)
        )

    async def GetStatCodes(self, request, context):
        self.logger.info("received GetStatCodesRequest")
        return StatCodesResponse(codes=["foo", "bar"])

    async def ValidateTicket(self, request, context):
        self.logger.info("received ValidateTicketRequest")
        return ValidateTicketResponse(valid_ticket=True)

    async def MakeMatches(self, request_iterator, context):
        async for request in request_iterator:
            if request.HasField("parameters"):
                self.logger.info("received MakeMatchesRequest(parameters)")
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
                    self.logger.info(
                        f"- updated shipCountMin: {self.ship_count_min} and shipCountMax: {self.ship_count_max}"
                    )
            elif request.HasField("ticket"):
                self.logger.info("received MakeMatchesRequest(ticket)")
                ticket = request.ticket
                self.unmatched_tickets.append(ticket)
                if len(self.unmatched_tickets) == self.ship_count_max:
                    match_response = make_match_response_from_tickets(
                        self.unmatched_tickets
                    )
                    self.unmatched_tickets.clear()
                    yield match_response
                self.logger.info(
                    f"- unmatched ticket size: {len(self.unmatched_tickets)}"
                )
            else:
                raise ValueError(request)
