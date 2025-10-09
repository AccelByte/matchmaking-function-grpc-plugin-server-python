from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BackfillMakeMatchesRequest(_message.Message):
    __slots__ = ["backfill_ticket", "parameters", "ticket"]
    class MakeMatchesParameters(_message.Message):
        __slots__ = ["rules", "scope", "tickId"]
        RULES_FIELD_NUMBER: _ClassVar[int]
        SCOPE_FIELD_NUMBER: _ClassVar[int]
        TICKID_FIELD_NUMBER: _ClassVar[int]
        rules: Rules
        scope: Scope
        tickId: int
        def __init__(self, scope: _Optional[_Union[Scope, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ..., tickId: _Optional[int] = ...) -> None: ...
    BACKFILL_TICKET_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    backfill_ticket: BackfillTicket
    parameters: BackfillMakeMatchesRequest.MakeMatchesParameters
    ticket: Ticket
    def __init__(self, parameters: _Optional[_Union[BackfillMakeMatchesRequest.MakeMatchesParameters, _Mapping]] = ..., backfill_ticket: _Optional[_Union[BackfillTicket, _Mapping]] = ..., ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class BackfillProposal(_message.Message):
    __slots__ = ["CreatedAt", "added_tickets", "attributes", "backfill_ticket_id", "match_pool", "match_session_id", "proposal_id", "proposed_teams"]
    class Team(_message.Message):
        __slots__ = ["parties", "team_id", "user_ids"]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    ADDED_TICKETS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    BACKFILL_TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    CreatedAt: _timestamp_pb2.Timestamp
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    MATCH_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PROPOSAL_ID_FIELD_NUMBER: _ClassVar[int]
    PROPOSED_TEAMS_FIELD_NUMBER: _ClassVar[int]
    added_tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
    attributes: _struct_pb2.Struct
    backfill_ticket_id: str
    match_pool: str
    match_session_id: str
    proposal_id: str
    proposed_teams: _containers.RepeatedCompositeFieldContainer[BackfillProposal.Team]
    def __init__(self, backfill_ticket_id: _Optional[str] = ..., CreatedAt: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., added_tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., proposed_teams: _Optional[_Iterable[_Union[BackfillProposal.Team, _Mapping]]] = ..., proposal_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., match_session_id: _Optional[str] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class BackfillResponse(_message.Message):
    __slots__ = ["backfill_proposal"]
    BACKFILL_PROPOSAL_FIELD_NUMBER: _ClassVar[int]
    backfill_proposal: BackfillProposal
    def __init__(self, backfill_proposal: _Optional[_Union[BackfillProposal, _Mapping]] = ...) -> None: ...

class BackfillTicket(_message.Message):
    __slots__ = ["CreatedAt", "match_pool", "match_session_id", "partial_match", "ticket_id"]
    class PartialMatch(_message.Message):
        __slots__ = ["backfill", "client_version", "match_attributes", "region_preferences", "server_name", "teams", "tickets"]
        BACKFILL_FIELD_NUMBER: _ClassVar[int]
        CLIENT_VERSION_FIELD_NUMBER: _ClassVar[int]
        MATCH_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
        REGION_PREFERENCES_FIELD_NUMBER: _ClassVar[int]
        SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
        TEAMS_FIELD_NUMBER: _ClassVar[int]
        TICKETS_FIELD_NUMBER: _ClassVar[int]
        backfill: bool
        client_version: str
        match_attributes: _struct_pb2.Struct
        region_preferences: _containers.RepeatedScalarFieldContainer[str]
        server_name: str
        teams: _containers.RepeatedCompositeFieldContainer[BackfillTicket.Team]
        tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
        def __init__(self, tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., teams: _Optional[_Iterable[_Union[BackfillTicket.Team, _Mapping]]] = ..., region_preferences: _Optional[_Iterable[str]] = ..., match_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., backfill: bool = ..., server_name: _Optional[str] = ..., client_version: _Optional[str] = ...) -> None: ...
    class Team(_message.Message):
        __slots__ = ["parties", "team_id", "user_ids"]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    CreatedAt: _timestamp_pb2.Timestamp
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    MATCH_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PARTIAL_MATCH_FIELD_NUMBER: _ClassVar[int]
    TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    match_pool: str
    match_session_id: str
    partial_match: BackfillTicket.PartialMatch
    ticket_id: str
    def __init__(self, ticket_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., CreatedAt: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., partial_match: _Optional[_Union[BackfillTicket.PartialMatch, _Mapping]] = ..., match_session_id: _Optional[str] = ...) -> None: ...

class EnrichTicketRequest(_message.Message):
    __slots__ = ["rules", "ticket"]
    RULES_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    rules: Rules
    ticket: Ticket
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class EnrichTicketResponse(_message.Message):
    __slots__ = ["ticket"]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    ticket: Ticket
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class GetStatCodesRequest(_message.Message):
    __slots__ = ["rules"]
    RULES_FIELD_NUMBER: _ClassVar[int]
    rules: Rules
    def __init__(self, rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class MakeMatchesRequest(_message.Message):
    __slots__ = ["parameters", "ticket"]
    class MakeMatchesParameters(_message.Message):
        __slots__ = ["rules", "scope", "tickId"]
        RULES_FIELD_NUMBER: _ClassVar[int]
        SCOPE_FIELD_NUMBER: _ClassVar[int]
        TICKID_FIELD_NUMBER: _ClassVar[int]
        rules: Rules
        scope: Scope
        tickId: int
        def __init__(self, scope: _Optional[_Union[Scope, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ..., tickId: _Optional[int] = ...) -> None: ...
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    parameters: MakeMatchesRequest.MakeMatchesParameters
    ticket: Ticket
    def __init__(self, parameters: _Optional[_Union[MakeMatchesRequest.MakeMatchesParameters, _Mapping]] = ..., ticket: _Optional[_Union[Ticket, _Mapping]] = ...) -> None: ...

class Match(_message.Message):
    __slots__ = ["backfill", "client_version", "match_attributes", "region_preferences", "server_name", "server_pool", "teams", "tickets"]
    class Team(_message.Message):
        __slots__ = ["parties", "team_id", "user_ids"]
        PARTIES_FIELD_NUMBER: _ClassVar[int]
        TEAM_ID_FIELD_NUMBER: _ClassVar[int]
        USER_IDS_FIELD_NUMBER: _ClassVar[int]
        parties: _containers.RepeatedCompositeFieldContainer[Party]
        team_id: str
        user_ids: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, user_ids: _Optional[_Iterable[str]] = ..., parties: _Optional[_Iterable[_Union[Party, _Mapping]]] = ..., team_id: _Optional[str] = ...) -> None: ...
    BACKFILL_FIELD_NUMBER: _ClassVar[int]
    CLIENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    MATCH_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    REGION_PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVER_POOL_FIELD_NUMBER: _ClassVar[int]
    TEAMS_FIELD_NUMBER: _ClassVar[int]
    TICKETS_FIELD_NUMBER: _ClassVar[int]
    backfill: bool
    client_version: str
    match_attributes: _struct_pb2.Struct
    region_preferences: _containers.RepeatedScalarFieldContainer[str]
    server_name: str
    server_pool: ServerPool
    teams: _containers.RepeatedCompositeFieldContainer[Match.Team]
    tickets: _containers.RepeatedCompositeFieldContainer[Ticket]
    def __init__(self, tickets: _Optional[_Iterable[_Union[Ticket, _Mapping]]] = ..., teams: _Optional[_Iterable[_Union[Match.Team, _Mapping]]] = ..., region_preferences: _Optional[_Iterable[str]] = ..., match_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., backfill: bool = ..., server_name: _Optional[str] = ..., client_version: _Optional[str] = ..., server_pool: _Optional[_Union[ServerPool, _Mapping]] = ...) -> None: ...

class MatchResponse(_message.Message):
    __slots__ = ["match"]
    MATCH_FIELD_NUMBER: _ClassVar[int]
    match: Match
    def __init__(self, match: _Optional[_Union[Match, _Mapping]] = ...) -> None: ...

class Party(_message.Message):
    __slots__ = ["party_id", "user_ids"]
    PARTY_ID_FIELD_NUMBER: _ClassVar[int]
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    party_id: str
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, party_id: _Optional[str] = ..., user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class Rules(_message.Message):
    __slots__ = ["json"]
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class Scope(_message.Message):
    __slots__ = ["ab_trace_id"]
    AB_TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    ab_trace_id: str
    def __init__(self, ab_trace_id: _Optional[str] = ...) -> None: ...

class ServerPool(_message.Message):
    __slots__ = ["claim_keys", "deployment", "server_provider"]
    CLAIM_KEYS_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_FIELD_NUMBER: _ClassVar[int]
    SERVER_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    claim_keys: _containers.RepeatedScalarFieldContainer[str]
    deployment: str
    server_provider: str
    def __init__(self, server_provider: _Optional[str] = ..., deployment: _Optional[str] = ..., claim_keys: _Optional[_Iterable[str]] = ...) -> None: ...

class StatCodesResponse(_message.Message):
    __slots__ = ["codes"]
    CODES_FIELD_NUMBER: _ClassVar[int]
    codes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, codes: _Optional[_Iterable[str]] = ...) -> None: ...

class Ticket(_message.Message):
    __slots__ = ["CreatedAt", "latencies", "match_pool", "namespace", "party_session_id", "players", "ticket_attributes", "ticket_id"]
    class LatenciesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    class PlayerData(_message.Message):
        __slots__ = ["attributes", "player_id"]
        ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
        PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
        attributes: _struct_pb2.Struct
        player_id: str
        def __init__(self, player_id: _Optional[str] = ..., attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    CREATEDAT_FIELD_NUMBER: _ClassVar[int]
    CreatedAt: _timestamp_pb2.Timestamp
    LATENCIES_FIELD_NUMBER: _ClassVar[int]
    MATCH_POOL_FIELD_NUMBER: _ClassVar[int]
    NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    PARTY_SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    TICKET_ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    TICKET_ID_FIELD_NUMBER: _ClassVar[int]
    latencies: _containers.ScalarMap[str, int]
    match_pool: str
    namespace: str
    party_session_id: str
    players: _containers.RepeatedCompositeFieldContainer[Ticket.PlayerData]
    ticket_attributes: _struct_pb2.Struct
    ticket_id: str
    def __init__(self, ticket_id: _Optional[str] = ..., match_pool: _Optional[str] = ..., CreatedAt: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., players: _Optional[_Iterable[_Union[Ticket.PlayerData, _Mapping]]] = ..., ticket_attributes: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., latencies: _Optional[_Mapping[str, int]] = ..., party_session_id: _Optional[str] = ..., namespace: _Optional[str] = ...) -> None: ...

class ValidateTicketRequest(_message.Message):
    __slots__ = ["rules", "ticket"]
    RULES_FIELD_NUMBER: _ClassVar[int]
    TICKET_FIELD_NUMBER: _ClassVar[int]
    rules: Rules
    ticket: Ticket
    def __init__(self, ticket: _Optional[_Union[Ticket, _Mapping]] = ..., rules: _Optional[_Union[Rules, _Mapping]] = ...) -> None: ...

class ValidateTicketResponse(_message.Message):
    __slots__ = ["valid_ticket"]
    VALID_TICKET_FIELD_NUMBER: _ClassVar[int]
    valid_ticket: bool
    def __init__(self, valid_ticket: bool = ...) -> None: ...
