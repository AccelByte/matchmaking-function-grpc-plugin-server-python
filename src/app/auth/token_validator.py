import asyncio
from datetime import datetime
from threading import RLock
from typing import Any, Dict, List, Optional

import jwt

import accelbyte_py_sdk.api.iam as iam_service
from accelbyte_py_sdk import AccelByteSDK
from accelbyte_py_sdk.core import Timer

from app.auth.bloom_filter import BloomFilter
from app.auth.errors import (
    FetchConfigurationError,
    FetchTokenGrantError,
    FetchJWKSError,
    FetchRevocationListError,
    FetchRoleError,
    InvalidTokenGrantError,
)
from app.auth.errors import (
    TokenKeyError,
    TokenPermissionError,
    TokenRevokedError,
    UserRevokedError,
)
from app.auth.models import Permission, Role


JWTClaims = Dict[str, Any]
NamespaceRole = Dict[str, str]
PublicPrivateKey = Any


class TokenValidator:
    DEFAULT_DECODE_ALGORITHMS: List[str] = ["RS256"]
    DEFAULT_DECODE_OPTIONS: Dict[str, Any] = {"verify_aud": False, "verify_exp": True}
    JWS_HEADER_PARAM_KEY_ID_KEY: str = "kid"
    JWKS_KEYS_KEY: str = "keys"

    def __init__(
        self,
        sdk: AccelByteSDK,
        publisher_namespace: Optional[str] = None,
        fetch_interval: float = 60.0,
    ) -> None:
        self.sdk: AccelByteSDK = sdk
        self.publisher_namespace: Optional[str] = publisher_namespace

        self._lock: RLock = RLock()

        self._cancelled: bool = False
        self._client_token: Optional[str] = None
        self._fetch_interval: float = fetch_interval
        self._jwks: Dict[str, PublicPrivateKey] = {}
        self._revoked_token_filter: Optional[BloomFilter] = None
        self._revoked_users = {}
        self._roles = {}
        self._task = None

    def __del__(self) -> None:
        self.cancel()

    async def initialize(self) -> None:
        await self.fetch_all()
        if self._task is None:
            self._task = asyncio.create_task(self._fetch_all_tail())

    def cancel(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

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
            leeway=1,
        )

        if sub := claims.get("sub"):
            claims["user_id"] = sub

        return claims

    async def fetch_all(self) -> None:
        await self.fetch_client_token()
        await self.fetch_jwks()  # TODO: fetch only an invalid 'kid' (key_id) is found
        await self.fetch_revocation_list()

    async def _fetch_all_tail(self) -> None:
        while not self._cancelled:
            await asyncio.sleep(self._fetch_interval)
            await self.fetch_all()

    async def fetch_client_token(self) -> None:
        result, error = await iam_service.token_grant_v3_async(
            grant_type="client_credentials",
            sdk=self.sdk,
        )
        if error:
            raise FetchTokenGrantError(error)

        if not result or not result.access_token:
            raise InvalidTokenGrantError()

        self.sdk.set_token(result)
        self._client_token = result.access_token

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

    async def get_role(self, role_id: str, force_fetch: bool = False) -> Role:
        if not force_fetch and (role := self._roles.get(role_id)):
            return role

        role, error = await iam_service.admin_get_role_v3_async(
            role_id=role_id, sdk=self.sdk
        )
        if error:
            raise FetchRoleError()

        self._roles[role_id] = role
        return role

    async def get_role_permissions(self, role_id: str) -> List[Permission]:
        role = await self.get_role(role_id=role_id)
        return role.permissions

    async def get_role_permissions_2(
        self, role_id: str, namespace: str, user_id: Optional[str] = None
    ) -> List[Permission]:
        permissions = await self.get_role_permissions(role_id=role_id)
        permissions = [
            Permission.create(
                action=p.action,
                resource=self.replace_resource(
                    resource=p.resource,
                    namespace=namespace,
                    user_id=user_id,
                ),
            )
            for p in permissions
        ]

        return permissions

    async def get_role_permissions_3(
        self, namespace_role: NamespaceRole, user_id: Optional[str] = None
    ) -> List[Permission]:
        permissions = await self.get_role_permissions_2(
            role_id=namespace_role.get("roleId"),
            namespace=namespace_role.get("namespace"),
            user_id=user_id,
        )

        return permissions

    async def has_valid_permissions(
        self,
        claims: JWTClaims,
        permission: Optional[Permission] = None,
        namespace: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        if permission is None:
            return True

        if not (token_namespace := claims.get("namespace")):
            return False

        modified_resource = self.replace_resource(
            resource=permission.resource,
            namespace=namespace,
            token_namespace=token_namespace,
            publisher_namespace=self.publisher_namespace,
            user_id=user_id,
        )

        # Check claim.permissions.
        origin_permissions = claims.get("permissions", [])
        origin_permissions = [
            Permission.create(
                action=p.get("Action"),  # case-senstive
                resource=p.get("Resource"),  # case-sensitive
            )
            for p in origin_permissions
        ]
        if origin_permissions and self.validate_permissions(
            permissions=origin_permissions,
            resource=modified_resource,
            action=permission.action,
        ):
            return True

        # Check claim.namespace_roles.
        claims_user_id = claims.get("user_id")
        namespace_roles = claims.get("namespace_roles")
        if claims_user_id and namespace_roles:
            role_namespace_permissions = []
            for namespace_role in namespace_roles:
                permissions = await self.get_role_permissions_3(
                    namespace_role=namespace_role, user_id=claims_user_id
                )
                role_namespace_permissions.extend(permissions)
            if role_namespace_permissions and self.validate_permissions(
                permissions=role_namespace_permissions,
                resource=modified_resource,
                action=permission.action,
            ):
                return True

        # Check claim.roles.
        roles = claims.get("roles")
        if roles:
            role_permissions = []
            for role_id in roles:
                permissions = await self.get_role_permissions_2(
                    role_id=role_id, namespace=token_namespace, user_id=user_id
                )
                role_permissions.extend(permissions)
            if role_permissions and self.validate_permissions(
                permissions=role_permissions,
                resource=modified_resource,
                action=permission.action,
            ):
                return True

        return False

    def is_token_revoked(self, token: str) -> bool:
        with self._lock:
            return self._revoked_token_filter.might_contains(key=token)

    def is_user_revoked(self, user_id: str, issued_at: int) -> bool:
        with self._lock:
            revoked_at = self._revoked_users.get(user_id)
            if revoked_at:
                return revoked_at >= issued_at
        return False

    async def validate(
        self,
        token: str,
        permission: Optional[Permission] = None,
        namespace: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[Exception]:
        claims = self.decode(token=token, **kwargs)

        if claims_user_id := claims.get("user_id"):
            if self.is_user_revoked(
                user_id=claims_user_id, issued_at=claims.get("iat")
            ):
                return UserRevokedError()

        if self.is_token_revoked(token=token):
            return TokenRevokedError()

        if not await self.has_valid_permissions(
            claims=claims, permission=permission, namespace=namespace, user_id=user_id
        ):
            return TokenPermissionError()

        return None

    @staticmethod
    def replace_resource(
        resource: str,
        namespace: Optional[str] = None,
        token_namespace: Optional[str] = None,
        publisher_namespace: Optional[str] = None,
        user_id: Optional[str] = None,
        cross_allowed: bool = False,
    ) -> str:
        modified_resource: str = resource

        if (
            cross_allowed
            and token_namespace is not None
            and (
                publisher_namespace == token_namespace
                or publisher_namespace == namespace
            )
        ):
            modified_resource = modified_resource.replace(
                "{namespace}", token_namespace
            )

        if namespace is not None:
            modified_resource = modified_resource.replace("{namespace}", namespace)

        if user_id is not None:
            modified_resource = modified_resource.replace("{userId}", user_id)

        return modified_resource

    @staticmethod
    def str2datetime(s: str) -> datetime:
        # from: 'YYYY-mm-ddTHH:MM:SS.fffffffffZ'
        # to:   'YYYY-mm-ddTHH:MM:SS.fffZ+0000'
        tz = "Z+0000" if s.endswith("Z") else ""  # Add explicit UTC timezone.
        s = s[0:23] + tz
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ%z")

    # TODO: write tests for validate_permissions(..)
    @staticmethod
    def validate_permissions(
        permissions: List[Permission], resource: str, action: int
    ) -> bool:
        if permissions:
            required_resource_items: List[str] = resource.split(":")
            for permission in permissions:
                has_resource_items: List[str] = permission.resource.split(":")

                has_resource_items_len = len(has_resource_items)
                required_resource_items_len = len(required_resource_items)
                min_length: int = min(
                    has_resource_items_len, required_resource_items_len
                )

                matches: bool = True
                for i in range(min_length):
                    s1: str = has_resource_items[i]
                    s2: str = required_resource_items[i]
                    if s1 != s2 and s1 != "*":
                        matches = False
                        break

                if matches:
                    if has_resource_items_len < required_resource_items_len:
                        if has_resource_items[-1] == "*":
                            if has_resource_items_len < 2:
                                matches = True
                            else:
                                segment: str = has_resource_items[-2]
                                if segment == "NAMESPACE" or segment == "USER":
                                    matches = False
                                else:
                                    matches = True
                        else:
                            matches = False
                        if not matches:
                            continue
                    elif has_resource_items_len > required_resource_items_len:
                        for i in range(
                            required_resource_items_len, has_resource_items_len
                        ):
                            if has_resource_items[i] != "*":
                                matches = False
                                break
                        if not matches:
                            continue

                    if (permission.action & action) > 0:
                        return True

        return False
