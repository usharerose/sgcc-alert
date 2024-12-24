"""
Trace request by ID
"""
import logging
from typing import Optional
import uuid

from flask import Flask, request

from .constants import DEFAULT_REQUEST_ID_HEADER


logger = logging.getLogger(__name__)


class RequestIdGenerator(object):

    def __init__(self, init_value: Optional[str] = None) -> None:
        self._init_value = init_value
        self._value: Optional[str] = init_value

    @property
    def request_id(self) -> str:
        if self._value is None:
            self._value = uuid.uuid4().hex
        return self._value


class TracingMiddleware(object):

    # pylint: disable=no-self-use
    def before_request(self) -> None:
        headers = request.headers

        # install request id
        original_request_id = headers.get(DEFAULT_REQUEST_ID_HEADER)
        request_id = RequestIdGenerator(original_request_id).request_id
        request.request_id = request_id  # type: ignore[attr-defined]

    @classmethod
    def install(cls, app: Flask) -> None:
        mw = cls()
        app.before_request(mw.before_request)
