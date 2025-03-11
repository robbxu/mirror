from typing import Any
from fastapi_users.exceptions import FastAPIUsersException
from enum import Enum


class UsernameAlreadyRegistered(FastAPIUsersException):
    pass

class EmailAlreadyRegistered(FastAPIUsersException):
    pass

class CompromisedRefreshToken(FastAPIUsersException):
    pass

class RefreshFailure(FastAPIUsersException):
    pass

class SubscriptionInitConflict(FastAPIUsersException):
    pass

class ErrorCode(str, Enum):
    REGISTER_EMAIL_ALREADY_EXISTS = "REGISTER_EMAIL_ALREADY_EXISTS"
    LOGIN_INVALID_SESSION = "LOGIN_INVALID_SESSION"
    LOGIN_BAD_CREDENTIALS = "LOGIN_BAD_CREDENTIALS"
    LOGOUT_INVALID_ID = "LOGOUT_INVALID_ID"
    TOKEN_REUSE = "TOKEN_REUSE"
    MALFORMED_QUERY = "MALFORMED_QUERY"
    OPTIMISTIC_LOCK = "STALE_DATA_RETRY"
