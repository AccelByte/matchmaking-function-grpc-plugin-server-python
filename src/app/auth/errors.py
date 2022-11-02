class FetchValidationDataError(Exception):
    pass


class FetchConfigurationError(FetchValidationDataError):
    pass


class FetchTokenGrantError(FetchValidationDataError):
    pass


class FetchJWKSError(FetchValidationDataError):
    pass


class FetchRevocationListError(FetchValidationDataError):
    pass


class FetchRoleError(FetchValidationDataError):
    pass


class InvalidTokenGrantError(FetchValidationDataError):
    pass


class TokenValidationError(Exception):
    pass


class TokenKeyError(TokenValidationError):
    pass


class TokenRevokedError(TokenValidationError):
    pass


class UserRevokedError(TokenValidationError):
    pass
