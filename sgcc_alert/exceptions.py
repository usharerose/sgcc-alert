"""
Exceptions
"""
from .constants import ERR_MSG_LOAD_RESIDENT_DETAILS_FAILED


class LoadResidentInfoError(Exception):

    def __init__(self, message: str = ERR_MSG_LOAD_RESIDENT_DETAILS_FAILED):
        super().__init__(message)
        self.message = message
