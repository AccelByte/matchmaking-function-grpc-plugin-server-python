# pylint: disable=not-an-iterable
# pylint: disable=no-member
# pylint: disable=no-name-in-module

import json

from logging import Logger, getLogger
from typing import Any, List, Optional

from grpc import StatusCode
from grpc.aio import AioRpcError, Metadata
from google.protobuf.json_format import MessageToDict

from app.proto.matchFunction_pb2 import Ticket
from app.proto.matchFunction_pb2 import GetStatCodesRequest, StatCodesResponse
from app.proto.matchFunction_pb2 import ValidateTicketRequest, ValidateTicketResponse
from app.proto.matchFunction_pb2 import EnrichTicketRequest, EnrichTicketResponse
from app.proto.matchFunction_pb2 import MakeMatchesRequest, MatchResponse
from app.proto.matchFunction_pb2 import BackfillMakeMatchesRequest, BackfillResponse
from app.proto.matchFunction_pb2_grpc import MatchFunctionServicer


class AsyncMatchFunctionService(MatchFunctionServicer):
    def __init__(
        self,
        logger: Optional[Logger] = None,
    ):
        self.logger = (
            logger if logger is not None else getLogger(self.__class__.__name__)
        )

    async def GetStatCodes(self, request, context):
        self.log_payload(f'{self.GetStatCodes.__name__} request: %s', request)
        assert isinstance(request, GetStatCodesRequest)
        response = StatCodesResponse(codes=[])
        self.log_payload(f'{self.GetStatCodes.__name__} response: %s', response)
        return response

    async def ValidateTicket(self, request, context):
        self.log_payload(f'{self.ValidateTicket.__name__} request: %s', request)
        assert isinstance(request, ValidateTicketRequest)
        response = ValidateTicketResponse(valid_ticket=True)
        self.log_payload(f'{self.ValidateTicket.__name__} response: %s', request)
        return response

    async def EnrichTicket(self, request, context):
        self.log_payload(f'{self.EnrichTicket.__name__} request: %s', request)
        assert isinstance(request, EnrichTicketRequest)
        response = EnrichTicketResponse()
        response.ticket.CopyFrom(request.ticket)
        if len(response.ticket.ticket_attributes) == 0:
            response.ticket.ticket_attributes["enrichedNumber"] = 20.0
            self.logger.info(
                "EnrichedTicket Attributes: {}".format(response.ticket.ticket_attributes)
            )
        self.log_payload(f'{self.EnrichTicket.__name__} response: %s', request)
        return response

    async def MakeMatches(self, request_iterator, context):
        first_message: bool = True
        matches_made: int = 0
        rules: Any = None
        unmatched_tickets: Optional[List[Ticket]] = None
        async for request in request_iterator:
            self.log_payload(f'{self.MakeMatches.__name__} request: %s', request)
            assert isinstance(request, MakeMatchesRequest)
            if first_message:
                first_message = False
                if not request.HasField("parameters"):
                    error = "First message must have the expected 'parameters' set."
                    self.logger.error(error)
                    raise self.create_aio_rpc_error(error, StatusCode.INVALID_ARGUMENT)
                rules = json.loads(request.parameters.rules.json)
                unmatched_tickets = []
            else:
                assert rules is not None
                assert unmatched_tickets is not None
                if not request.HasField("ticket"):
                    error = "Message must have the expected 'ticket' set."
                    self.logger.error(error)
                    raise self.create_aio_rpc_error(error, StatusCode.INVALID_ARGUMENT)
                match_ticket = Ticket()
                match_ticket.CopyFrom(request.ticket)
                unmatched_tickets.append(match_ticket)
                if len(unmatched_tickets) == 2:
                    self.logger.info("Received enough tickets to create a match!")
                    player_ids = []
                    response = MatchResponse()
                    for unmatched_ticket in unmatched_tickets:
                        for player in unmatched_ticket.players:
                            player_ids.append(player.player_id)
                        response.match.tickets.append(unmatched_ticket)
                    unmatched_tickets.clear()
                    response.match.teams.add().user_ids.extend(player_ids)

                    # RegionPreference value is just an example. The value(s) should be from the best region on the matchmaker.Ticket.Latencies
                    response.match.region_preferences.append("us-east-2")
                    response.match.region_preferences.append("us-west-2")
                    
                    self.logger.info("Match made and sent to client!")
                    self.log_payload(f'{self.MakeMatches.__name__} response: %s', response)
                    yield response
                    matches_made += 1
                else:
                    self.logger.info("Not enough tickets to create a match: {}".format(len(unmatched_tickets)))
        self.logger.info("Received MakeMatches (end): {} match(es) made".format(matches_made))

    async def BackfillMatches(self, request_iterator, context):
        async for request in request_iterator:
            self.log_payload(f'{self.BackfillMatches.__name__} request: %s', request)
            assert isinstance(request, BackfillMakeMatchesRequest)
            if request.HasField("backfill_ticket"):
                response = BackfillResponse()
                self.log_payload(f'{self.BackfillMatches.__name__} response: %s', response)
                yield response
        self.logger.info("received BackfillMatches (end)")

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
        
    def log_payload(self, format : str, payload):
        if not self.logger:
            return
        payload_dict = MessageToDict(payload, preserving_proto_field_name=True)
        payload_json = json.dumps(payload_dict)
        self.logger.info(format % payload_json)
