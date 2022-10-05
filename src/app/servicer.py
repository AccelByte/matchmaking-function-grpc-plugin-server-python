import google.protobuf.struct_pb2 as struct_proto
import google.protobuf.timestamp_pb2 as timestamp_proto

import app.proto.matchFunction_pb2_grpc as match_func_grpc
import app.proto.matchFunction_pb2 as match_func_proto


class MatchFunctionServicer(match_func_grpc.MatchFunctionServicer):

    def GetStatCodes(self, request, context):
        return match_func_proto.StatCodesResponse(
            codes=["foo", "bar"]
        )

    def ValidateTicket(self, request, context):
        return match_func_proto.ValidateTicketResponse(
            valid=True
        )

    def MakeMatches(self, request_iterator, context):
        for request in request_iterator:
            created_at = timestamp_proto.Timestamp()
            created_at.GetCurrentTime()
            player_attributes = struct_proto.Struct()
            player_attributes.update({
                "bar": "bar",
            })
            players = [
                match_func_proto.Ticket.PlayerData(
                    player_id="foo",
                    attributes=player_attributes,
                )
            ]
            ticket_attributes = struct_proto.Struct()
            ticket_attributes.update({
                "foo": "foo",
            })
            match_attributes = struct_proto.Struct()
            match_attributes.update({
                "foo": "foo",
            })
            yield match_func_proto.MatchResponse(
                match=match_func_proto.Match(
                    tickets=[
                        match_func_proto.Ticket(
                            ticket_id="foo",
                            match_pool="foo",
                            CreatedAt=created_at,
                            players=players,
                            ticket_attributes=ticket_attributes,
                            latencies={
                                "foo": 0,
                            }
                        )
                    ],
                    teams=[
                        match_func_proto.Match.Team(
                            user_ids=[
                                "foo",
                                "bar",
                            ]
                        )
                    ],
                    region_preferences=[
                        "us-east",
                        "us-west",
                    ],
                    match_attributes=match_attributes,
                )
            )
