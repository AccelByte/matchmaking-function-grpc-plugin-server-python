# Copyright (c) 2025 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

# pylint: disable=not-an-iterable
# pylint: disable=no-member
# pylint: disable=no-name-in-module

import json
from datetime import datetime, timezone
from logging import Logger
from typing import List, Optional, Tuple
from uuid import uuid4

from grpc import ServicerContext, StatusCode
from google.protobuf.json_format import MessageToJson
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from accelbyte_py_sdk import AccelByteSDK

from matchFunction_pb2 import (
    BackfillTicket,
    BackfillProposal,
    Match,
    Ticket,
    GetStatCodesRequest, StatCodesResponse,
    ValidateTicketRequest, ValidateTicketResponse,
    EnrichTicketRequest, EnrichTicketResponse,
    MakeMatchesRequest, MatchResponse,
    BackfillMakeMatchesRequest, BackfillResponse,
    DESCRIPTOR,
)
from matchFunction_pb2_grpc import MatchFunctionServicer

from ..ctypes import GameRules, ValidationError


class AsyncMatchFunctionService(MatchFunctionServicer):
    full_name: str = DESCRIPTOR.services_by_name["MatchFunction"].full_name

    def __init__(
        self,
        sdk: Optional[AccelByteSDK] = None,
        logger: Optional[Logger] = None,
    ):
        self.sdk = sdk
        self.logger = logger

    async def GetStatCodes(self, request: GetStatCodesRequest, context: ServicerContext):
        self.log_payload(f'{self.GetStatCodes.__name__} request: %s', request)

        try:
            rules_json = request.rules.json or "{}"
            rules_obj = json.loads(rules_json)
            rules = GameRules(**rules_obj)
        except ValidationError as error:
            self.logger.error(error)
            await context.abort(StatusCode.INVALID_ARGUMENT, details=str(error))

        response = StatCodesResponse(codes=[])

        self.log_payload(f'{self.GetStatCodes.__name__} response: %s', response)
        return response

    async def ValidateTicket(self, request, context: ServicerContext):
        self.log_payload(f'{self.ValidateTicket.__name__} request: %s', request)
        assert isinstance(request, ValidateTicketRequest)
        response = ValidateTicketResponse(valid_ticket=True)
        self.log_payload(f'{self.ValidateTicket.__name__} response: %s', request)
        return response

    async def EnrichTicket(self, request, context: ServicerContext):
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

    async def MakeMatches(self, request_iterator, context: ServicerContext):
        first_message: bool = True
        matches_made: int = 0
        rules: Optional[GameRules] = None
        unmatched_tickets: Optional[List[Ticket]] = None
        async for request in request_iterator:
            self.log_payload(f'{self.MakeMatches.__name__} request: %s', request)
            assert isinstance(request, MakeMatchesRequest)
            if first_message:
                first_message = False
                if not request.HasField("parameters"):
                    error = "First message must have the expected 'parameters' set."
                    self.logger.error(error)
                    await context.abort(StatusCode.INVALID_ARGUMENT, details=error)
                try:
                    parameters = request.parameters
                    rules_json = parameters.rules.json or "{}"
                    rules_obj = json.loads(rules_json)
                    rules = GameRules(**rules_obj)
                    unmatched_tickets = []
                except ValidationError as error:
                    self.logger.error(error)
                    await context.abort(StatusCode.INVALID_ARGUMENT, details=str(error))
            else:
                assert rules is not None
                assert unmatched_tickets is not None
                if not request.HasField("ticket"):
                    error = "Message must have the expected 'ticket' set."
                    self.logger.error(error)
                    await context.abort(StatusCode.INVALID_ARGUMENT, details=error)

                ticket = request.ticket
                matches, unmatched_tickets = self.build_match(
                    rules=rules,
                    ticket=ticket,
                    unmatched_tickets=unmatched_tickets,
                )
                if matches:
                    for match in matches:
                        response = MatchResponse()
                        response.match = match
                        self.logger.info("Match made and sent to client!")
                        self.log_payload(f'{self.MakeMatches.__name__} response: %s', response)
                        yield response
                        matches_made += 1
                else:
                    self.logger.info("Not enough tickets to create a match: {}".format(len(unmatched_tickets)))
        self.logger.info("Received MakeMatches (end): {} match(es) made".format(matches_made))

    def build_match(
        self, rules: GameRules, ticket: Ticket, unmatched_tickets: List[Ticket],
    ) -> Tuple[List[Match], List[Ticket]]:
        matches: List[Match] = []

        unmatched_tickets.append(ticket)

        min_players = rules.alliance.min_number * rules.alliance.player_min_number
        max_players = rules.alliance.max_number * rules.alliance.player_max_number

        if min_players == 0 and max_players == 0:
            min_players = 2
            max_players = 2

        if rules.shipCountMin != 0:
            min_players *= rules.shipCountMin

        if rules.shipCountMax != 0:
            min_players *= rules.shipCountMax

        while True:
            if len(unmatched_tickets) < min_players:
                break

            num_players = min_players
            if len(unmatched_tickets) >= max_players:
                num_players = max_players

            self.logger.info("Received enough tickets to create a match!")

            backfill = False
            if rules.auto_backfill and num_players < max_players:
                backfill = True

            players = []
            player_ids = []
            matched_tickets = []
            for i in range(num_players):
                player: Ticket.PlayerData = Ticket.PlayerData()
                matched_ticket = unmatched_tickets[i]
                for player in matched_ticket.players:
                    assert isinstance(player, Ticket.PlayerData)
                    players.append(player)
                    player_ids.append(player.player_id)
                matched_tickets.append(matched_ticket)

            team_id = str(uuid4())
            team = Match.Team()
            team.team_id = team_id
            team.user_ids.extend(player_ids)

            match = Match()
            match.tickets.extend(matched_tickets)
            match.teams.append(team)
            match.match_attributes.fields["small-team-1"].string_value = team_id
            match.backfill = backfill
            # RegionPreference value is just an example.
            # The value(s) should be from the best region on the matchmaker.Ticket.Latencies
            match.region_preferences.extend(["us-east-2", "us-west-2"])

            unmatched_tickets = unmatched_tickets[num_players:]

            matches.append(match)

        return matches, unmatched_tickets

    async def BackfillMatches(self, request_iterator, context: ServicerContext):
        first_message: bool = True
        proposals_made: int = 0
        rules: Optional[GameRules] = None
        unmatched_tickets: Optional[List[Ticket]] = None
        unmatched_backfill_tickets: Optional[List[BackfillTicket]] = None
        async for request in request_iterator:
            self.log_payload(f'{self.BackfillMatches.__name__} request: %s', request)
            assert isinstance(request, BackfillMakeMatchesRequest)
            if first_message:
                first_message = False
                if not request.HasField("parameters"):
                    error = "First message must have the expected 'parameters' set."
                    self.logger.error(error)
                    await context.abort(StatusCode.INVALID_ARGUMENT, details=error)
                try:
                    parameters = request.parameters
                    rules_json = parameters.rules.json or "{}"
                    rules_obj = json.loads(rules_json)
                    rules = GameRules(**rules_obj)
                    unmatched_tickets = []
                    unmatched_backfill_tickets = []
                except ValidationError as error:
                    self.logger.error(error)
                    await context.abort(StatusCode.INVALID_ARGUMENT, details=str(error))
            else:
                assert rules is not None
                assert unmatched_tickets is not None
                assert unmatched_backfill_tickets is not None
                if request.HasField("ticket"):
                    ticket = request.ticket
                    proposals, unmatched_tickets, unmatched_backfill_tickets = self.build_backfill_match(
                        rules=rules,
                        ticket=ticket,
                        unmatched_tickets=unmatched_tickets,
                        backfill_ticket=None,
                        unmatched_backfill_tickets=unmatched_backfill_tickets,
                    )
                    if proposals:
                        for proposal in proposals:
                            response = BackfillResponse()
                            response.backfill_proposal = proposal
                            self.logger.info("Backfill proposal made and sent to client!")
                            self.log_payload(f'{self.BackfillMatches.__name__} response: %s', response)
                            yield response
                            proposals_made += 1
                    else:
                        self.logger.info(
                            "Not enough tickets to create a backfill proposal: {}, {}".format(
                                len(unmatched_tickets),
                                len(unmatched_backfill_tickets),
                            )
                        )
                elif request.HasField("backfill_ticket"):
                    backfill_ticket = request.backfill_ticket
                    proposals, unmatched_tickets, unmatched_backfill_tickets = self.build_backfill_match(
                        rules=rules,
                        ticket=None,
                        unmatched_tickets=unmatched_tickets,
                        backfill_ticket=backfill_ticket,
                        unmatched_backfill_tickets=unmatched_backfill_tickets,
                    )
                    if proposals:
                        for proposal in proposals:
                            response = BackfillResponse()
                            response.backfill_proposal = proposal
                            self.logger.info("Backfill proposal made and sent to client!")
                            self.log_payload(f'{self.BackfillMatches.__name__} response: %s', response)
                            yield response
                            proposals_made += 1
                    else:
                        self.logger.info(
                            "Not enough tickets to create a backfill proposal: {}, {}".format(
                                len(unmatched_tickets),
                                len(unmatched_backfill_tickets),
                            )
                        )

        self.logger.info("received BackfillMatches (end): {} proposal(s) made".format(proposals_made))

    def build_backfill_match(
        self, rules: GameRules,
        ticket: Optional[Ticket], unmatched_tickets: List[Ticket],
        backfill_ticket: Optional[BackfillTicket], unmatched_backfill_tickets: List[BackfillTicket],
    ) -> Tuple[List[BackfillProposal], List[Ticket], List[BackfillTicket]]:
        proposals: List[BackfillProposal] = []

        if ticket:
            unmatched_tickets.append(ticket)

        if backfill_ticket:
            unmatched_backfill_tickets.append(backfill_ticket)

        if len(unmatched_tickets) > 0 and len(unmatched_backfill_tickets) > 0:
            self.logger.info("Received enough tickets to backfill!")

            len_unmatched_backfill_tickets = len(unmatched_backfill_tickets)
            for i in range(len_unmatched_backfill_tickets):
                b = unmatched_backfill_tickets[i]
                t = unmatched_tickets[0]
                unmatched_tickets = unmatched_tickets[1:]

                team_id = str(uuid4())
                team = BackfillProposal.Team()
                team.team_id = team_id

                created_at = Timestamp()
                created_at.FromDateTime(datetime.now(timezone.utc))

                attributes = Struct()
                attributes.update(b.partial_match.match_attributes)
                attributes.update({"generatedID": str(uuid4())})

                proposal = BackfillProposal()
                proposal.backfill_ticket_id = b.ticket_id
                proposal.CreatedAt = created_at
                proposal.added_tickets.append(t)
                proposal.proposed_teams.extend(b.partial_match.teams)
                proposal.proposed_teams.append(team)
                proposal.proposal_id = str(uuid4())
                proposal.match_pool = b.match_pool
                proposal.match_session_id = b.match_session_id
                proposal.attributes = attributes

                proposals.append(proposal)

                if len(unmatched_tickets) == 0:
                    if i+1 < len(unmatched_backfill_tickets):
                        unmatched_backfill_tickets = unmatched_backfill_tickets[i+1:]
                    else:
                        unmatched_backfill_tickets = []
                    break

        return proposals, unmatched_tickets, unmatched_backfill_tickets

    # noinspection PyShadowingBuiltins
    def log_payload(self, format : str, payload):
        if not self.logger:
            return
        payload_json = MessageToJson(payload, preserving_proto_field_name=True)
        self.logger.info(format.format(payload_json))
