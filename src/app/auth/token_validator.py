from datetime import datetime
from threading import RLock
from typing import Any, Dict, List, Optional

import jwt

import accelbyte_py_sdk.api.iam as iam_service
from accelbyte_py_sdk import AccelByteSDK

from app.auth.bloom_filter import BloomFilter


JWTClaims = Dict[str, Any]
PublicPrivateKey = Any


class FetchValidationDataError(Exception):
    pass


class FetchConfigurationError(FetchValidationDataError):
    pass


class FetchJWKSError(FetchValidationDataError):
    pass


class FetchRevocationListError(FetchValidationDataError):
    pass


class TokenValidationError(Exception):
    pass


class TokenRevokedError(TokenValidationError):
    pass


class UserRevokedError(TokenValidationError):
    pass


class TokenValidator:
    DEFAULT_DECODE_ALGORITHMS: List[str] = ["RS256"]
    DEFAULT_DECODE_OPTIONS: Dict[str, Any] = {"verify_aud": False, "verify_exp": True}
    JWS_HEADER_PARAM_KEY_ID_KEY: str = "kid"
    JWKS_KEYS_KEY: str = "keys"

    def __init__(
        self,
        sdk: AccelByteSDK,
    ) -> None:
        self.sdk: AccelByteSDK = sdk
        self._jwks: Dict[str, PublicPrivateKey] = {}
        self._lock: RLock = RLock()
        self._revoked_token_filter: Optional[BloomFilter] = None
        self._revoked_users = {}

    async def initialize(self) -> None:
        await self.fetch_jwks()
        await self.fetch_revocation_list()

    async def fetch_jwks(self) -> None:
        result, error = await iam_service.get_jwksv3_async(sdk=self.sdk)
        if error:
            raise FetchJWKSError(error)

        with self._lock:
            keys = result.to_dict().get(self.JWKS_KEYS_KEY, [])
            jwks = jwt.PyJWKSet(keys)
            for jwk in jwks.keys:
                self._jwks[jwk.key_id] = jwk.key

    async def fetch_revocation_list(self) -> None:
        # TODO: fix security of GetRevocationListV3
        from accelbyte_py_sdk.core import create_basic_authentication

        client_auth, error = self.sdk.get_client_auth()
        if error:
            raise FetchConfigurationError(error)
        basic_authentication = create_basic_authentication(*client_auth)

        result, error = await iam_service.get_revocation_list_v3_async(
            sdk=self.sdk, x_additional_headers={"Authorization": basic_authentication}
        )
        if error:
            raise FetchRevocationListError(error)

        with self._lock:
            # Revoked Tokens
            revoked_tokens = result.revoked_tokens
            self._revoked_token_filter = BloomFilter.create_from_bits(
                bits=revoked_tokens.bits, k=revoked_tokens.k, m=revoked_tokens.m
            )
            # Revoked Users
            revoked_users = result.revoked_users
            self._revoked_users = {}
            for user in revoked_users:
                if user.id_ and user.revoked_at:
                    revoked_at = self.str2datetime(user.revoked_at).timestamp()
                    self._revoked_users[user.id_] = revoked_at

    def decode(
        self,
        token: str,
        decode_algorithms: Optional[List[str]] = None,
        decode_options: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> JWTClaims:
        decode_algorithms = (
            decode_algorithms
            if decode_algorithms is not None
            else self.DEFAULT_DECODE_ALGORITHMS
        )
        decode_options = (
            decode_options
            if decode_options is not None
            else self.DEFAULT_DECODE_OPTIONS
        )

        header_params = jwt.get_unverified_header(jwt=token)
        if not (kid := header_params.get(self.JWS_HEADER_PARAM_KEY_ID_KEY)):
            raise KeyError(self.JWS_HEADER_PARAM_KEY_ID_KEY)

        if not (key := self._jwks.get(kid)):
            raise KeyError(kid)

        claims = jwt.decode(
            jwt=token,
            key=key,
            algorithms=decode_algorithms,
            options=decode_options,
        )

        if sub := claims.get("sub"):
            claims["user_id"] = sub

        return claims

    def is_token_revoked(self, token: str) -> bool:
        with self._lock:
            return self._revoked_token_filter.might_contains(key=token)

    def is_user_revoked(self, user_id: str, issued_at: int) -> bool:
        with self._lock:
            revoked_at = self._revoked_users.get(user_id)
            if revoked_at:
                return revoked_at >= issued_at
        return False

    def validate(self, token: str, **kwargs) -> bool:
        claims = self.decode(token=token, **kwargs)

        iat = claims["iat"]
        sub = claims["sub"]
        if self.is_user_revoked(user_id=sub, issued_at=iat):
            raise UserRevokedError()

        if self.is_token_revoked(token=token):
            raise TokenRevokedError()

        return True

    @staticmethod
    def str2datetime(s: str) -> datetime:
        # from: 'YYYY-mm-ddTHH:MM:SS.fffffffffZ'
        # to:   'YYYY-mm-ddTHH:MM:SS.fffZ+0000'
        tz = "Z+0000" if s.endswith("Z") else ""  # Add explicit UTC timezone.
        s = s[0:23] + tz
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ%z")
