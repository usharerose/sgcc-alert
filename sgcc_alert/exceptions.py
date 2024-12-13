"""
Exceptions
"""
from .constants import (
    ERR_MSG_CAPTCHA_WRONG,
    ERR_MSG_LOAD_RESIDENT_DETAILS_FAILED,
    ERR_MSG_LOAD_DATA_TABLE_TIMEOUT,
    ERR_MSG_REACH_LOGIN_LIMIT,
    ERR_MSG_WRONG_ACCOUNT_PWD
)


class LoadResidentInfoError(Exception):

    def __init__(self, message: str = ERR_MSG_LOAD_RESIDENT_DETAILS_FAILED):
        super().__init__(message)
        self.message = message


class LoginError(Exception):

    pass


class CaptchaValidationError(LoginError):

    def __init__(self, message: str = ERR_MSG_CAPTCHA_WRONG):
        super().__init__(message)
        self.message = message


class LoginRateLimitError(LoginError):

    def __init__(self, message: str = ERR_MSG_REACH_LOGIN_LIMIT):
        super().__init__(message)
        self.message = message


class LoginAccountPasswordError(LoginError):

    def __init__(self, message: str = ERR_MSG_WRONG_ACCOUNT_PWD):
        super().__init__(message)
        self.message = message


class LoadTableTimeoutError(Exception):

    def __init__(self, message: str = ERR_MSG_LOAD_DATA_TABLE_TIMEOUT):
        super().__init__(message)
        self.message = message
