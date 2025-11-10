import datetime

from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetStatCodesRequest(_message.Message):
    __slots__ = ("rules",)
    RULES_FIELD_NUMBER: _ClassVar[int]
    rules: Rules
    def __init__(self, rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class StatCodesResponse(_message.Message):
    __slots__ = ("codes",)
    CODES_FIELD_NUMBER: _ClassVar[int]
    codes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, codes: _Optional[_Iterable[str]] = ...) -> None: ...

class ValidateTicketRequest(_message.Message):
    __slots__ = ("ticket", "rules")
    TICKET_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    ticket: Ticket
    rules: Rules
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class ValidateTicketResponse(_message.Message):
    __slots__ = ("valid_ticket",)
    VALID_TICKET_FIELD_NUMBER: _ClassVar[int]
    valid_ticket: bool
    def __init__(self, valid_ticket: bool = ...) -> None: ...

class EnrichTicketRequest(_message.Message):
    __slots__ = ("ticket", "rules")
    TICKET_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    ticket: Ticket
    rules: Rules
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class EnrichTicketResponse(_message.Message):
    __slots__ = ("ticket",)
    TICKET_FIELD_NUMBER: _ClassVar[int]
    ticket: Ticket
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class MakeMatchesRequest(_message.Message):
    __slots__ = ("parameters", "ticket")
    class MakeMatchesParameters(_message.Message):
        __slots__ = ("scope", "rules", "tickId")
        SCOPE_FIELD_NUMBER: _ClassVar[int]
        RULES_FIELD_NUMBER: _ClassVar[int]
        TICKID_FIELD_NUMBER: _ClassVar[int]
        scope: Scope
        rules: Rules
        tickId: int
        def __init__(self, scope: _Optional[_Union[Scope, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ..., tickId: _Optional[int] = ...) -> None: ...
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    parameters: MakeMatchesRequest.MakeMatchesParameters
    ticket: Ticket
    def __init__(self, parameters: _Optional[_Union[MakeMatchesRequest.MakeMatchesParameters, _Mapping]] = ..., ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class MatchResponse(_message.Message):
    __slots__ = ("match",)
    MATCH_FIELD_NUMBER: _ClassVar[int]
    match: Match
    def __init__(self, match: _Optional[_Union[Match, _Mapping]] = ...) -> None: ...

class Scope(_message.Message):
    __slots__ = ("ab_trace_id",)
    AB_TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    ab_trace_id: str
    def __init__(self, ab_trace_id: _Optional[str] = ...) -> None: ...

class Rules(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class Party(_message.Message):
    __slots__ = ("party_id", "user_ids")
    PARTY_ID_FIELD_NUMBER: _ClassVar[int]
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    party_id: str
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, party_id: _Optional[str] = ..., user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class Match(_message.Message):
    __slots__ = ("tickets", "teams", "region_preferences", "match_attributes", "backfill", "server_name", "client_version", "server_pool")
    class Team(_message.Message):
        __slots__ = ("user_ids", "parties", "team_id")
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    TICKETS_FIELD_NUMBER: _ClassVar[int]
    TEAMS_FIELD_NUMBER: _ClassVar[int]
    REGION_PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    MATCH_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    BACKFILL_FIELD_NUMBER: _ClassVar[int]
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    CLIENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    SERVER_POOL_FIELD_NUMBER: _ClassVar[int]
    tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
    teams: _containers.RepeatedCompositeFieldContainer[Match.Team]
    region_preferences: _containers.RepeatedScalarFieldContainer[str]
    match_attributes: _struct_pb2.Struct
    backfill: bool
    server_name: str
    client_version: str
    server_pool: ServerPool
    def __init__(self, tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., teams: _Optional[_Iterable[_Union[Match.Team, _Mapping]]] = ..., region_preferences: _Optional[_Iterable[str]] = ..., match_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., backfill: bool = ..., server_name: _Optional[str] = ..., client_version: _Optional[str] = ..., server_pool: _Optional[_Union[ServerPool, _Mapping]] = ...) -> None: ...

class ServerPool(_message.Message):
    __slots__ = ("server_provider", "deployment", "claim_keys")
    SERVER_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_FIELD_NUMBER: _ClassVar[int]
    CLAIM_KEYS_FIELD_NUMBER: _ClassVar[int]
    server_provider: str
    deployment: str
    claim_keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, server_provider: _Optional[str] = ..., deployment: _Optional[str] = ..., claim_keys: _Optional[_Iterable[str]] = ...) -> None: ...

class Ticket(_message.Message):
    __slots__ = ("ticket_id", "match_pool", "CreatedAt", "players", "ticket_attributes", "latencies", "party_session_id", "namespace")
    class PlayerData(_message.Message):
        __slots__ = ("player_id", "attributes")
        PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
        ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
        player_id: str
        attributes: _struct_pb2.Struct
        def __init__(self, player_id: _Optional[str] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    class LatenciesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    TICKET_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    LATENCIES_FIELD_NUMBER: _ClassVar[int]
    PARTY_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    ticket_id: str
    match_pool: str
    CreatedAt: _timestamp_pb2.Timestamp
    players: _containers.RepeatedCompositeFieldContainer[Ticket.PlayerData]
    ticket_attributes: _struct_pb2.Struct
    latencies: _containers.ScalarMap[str, int]
    party_session_id: str
    namespace: str
    def __init__(self, ticket_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., CreatedAt: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., players: _Optional[_Iterable[_Union[Ticket.PlayerData, _Mapping]]] = ..., ticket_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., latencies: _Optional[_Mapping[str, int]] = ..., party_session_id: _Optional[str] = ..., namespace: _Optional[str] = ...) -> None: ...

class BackfillProposal(_message.Message):
    __slots__ = ("backfill_ticket_id", "CreatedAt", "added_tickets", "proposed_teams", "proposal_id", "match_pool", "match_session_id")
    class Team(_message.Message):
        __slots__ = ("user_ids", "parties", "team_id")
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    BACKFILL_TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    ADDED_TICKETS_FIELD_NUMBER: _ClassVar[int]
    PROPOSED_TEAMS_FIELD_NUMBER: _ClassVar[int]
    PROPOSAL_ID_FIELD_NUMBER: _ClassVar[int]
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    MATCH_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    backfill_ticket_id: str
    CreatedAt: _timestamp_pb2.Timestamp
    added_tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
    proposed_teams: _containers.RepeatedCompositeFieldContainer[BackfillProposal.Team]
    proposal_id: str
    match_pool: str
    match_session_id: str
    def __init__(self, backfill_ticket_id: _Optional[str] = ..., CreatedAt: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., added_tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., proposed_teams: _Optional[_Iterable[_Union[BackfillProposal.Team, _Mapping]]] = ..., proposal_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., match_session_id: _Optional[str] = ...) -> None: ...

class BackfillMakeMatchesRequest(_message.Message):
    __slots__ = ("parameters", "backfill_ticket", "ticket")
    class MakeMatchesParameters(_message.Message):
        __slots__ = ("scope", "rules", "tickId")
        SCOPE_FIELD_NUMBER: _ClassVar[int]
        RULES_FIELD_NUMBER: _ClassVar[int]
        TICKID_FIELD_NUMBER: _ClassVar[int]
        scope: Scope
        rules: Rules
        tickId: int
        def __init__(self, scope: _Optional[_Union[Scope, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ..., tickId: _Optional[int] = ...) -> None: ...
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    BACKFILL_TICKET_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    parameters: BackfillMakeMatchesRequest.MakeMatchesParameters
    backfill_ticket: BackfillTicket
    ticket: Ticket
    def __init__(self, parameters: _Optional[_Union[BackfillMakeMatchesRequest.MakeMatchesParameters, _Mapping]] = ..., backfill_ticket: _Optional[_Union[BackfillTicket, _Mapping]] = ..., ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class BackfillResponse(_message.Message):
    __slots__ = ("backfill_proposal",)
    BACKFILL_PROPOSAL_FIELD_NUMBER: _ClassVar[int]
    backfill_proposal: BackfillProposal
    def __init__(self, backfill_proposal: _Optional[_Union[BackfillProposal, _Mapping]] = ...) -> None: ...

class BackfillTicket(_message.Message):
    __slots__ = ("ticket_id", "match_pool", "CreatedAt", "partial_match", "match_session_id")
    class Team(_message.Message):
        __slots__ = ("user_ids", "parties", "team_id")
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    class PartialMatch(_message.Message):
        __slots__ = ("tickets", "teams", "region_preferences", "match_attributes", "backfill", "server_name", "client_version")
        TICKETS_FIELD_NUMBER: _ClassVar[int]
        TEAMS_FIELD_NUMBER: _ClassVar[int]
        REGION_PREFERENCES_FIELD_NUMBER: _ClassVar[int]
        MATCH_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
        BACKFILL_FIELD_NUMBER: _ClassVar[int]
        SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
        CLIENT_VERSION_FIELD_NUMBER: _ClassVar[int]
        tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
        teams: _containers.RepeatedCompositeFieldContainer[BackfillTicket.Team]
        region_preferences: _containers.RepeatedScalarFieldContainer[str]
        match_attributes: _struct_pb2.Struct
        backfill: bool
        server_name: str
        client_version: str
        def __init__(self, tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., teams: _Optional[_Iterable[_Union[BackfillTicket.Team, _Mapping]]] = ..., region_preferences: _Optional[_Iterable[str]] = ..., match_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., backfill: bool = ..., server_name: _Optional[str] = ..., client_version: _Optional[str] = ...) -> None: ...
    TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_MATCH_FIELD_NUMBER: _ClassVar[int]
    MATCH_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ticket_id: str
    match_pool: str
    CreatedAt: _timestamp_pb2.Timestamp
    partial_match: BackfillTicket.PartialMatch
    match_session_id: str
    def __init__(self, ticket_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., CreatedAt: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., partial_match: _Optional[_Union[BackfillTicket.PartialMatch, _Mapping]] = ..., match_session_id: _Optional[str] = ...) -> None: ...
