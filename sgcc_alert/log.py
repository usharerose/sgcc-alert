"""
System logger configurations

User only needs to call 'config_logging' before logging
"""
import copy
import datetime
import json
import logging
from logging import Filter, Formatter, LogRecord
from logging.config import dictConfig
from collections import OrderedDict
from typing import Optional, Sequence

import flask
from flask import Flask, request
from flask.typing import ResponseClass
import tzlocal


logger = logging.getLogger(__name__)


__all__ = [
    'config_logging',
    'LoggingMiddleware'
]


DEFAULT_LOG_CONFIG_DICT = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': (
                '%(asctime)s | %(service_name)s | %(process)d | %(thread)d | '
                '%(levelname)s | +%(lineno)d %(name)s | %(request_id)s '
                '|> %(message)s'
            ),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'sgcc_alert.log.JsonFormatter'
        }
    },
    'filters': {
        'request_id_filter': {
            '()': 'sgcc_alert.log.RequestIdFilter'
        },
        'service_name_filter': {
            '()': 'sgcc_alert.log.ServiceNameFilter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
            'filters': [
                'request_id_filter',
                'service_name_filter'
            ]
        },
        'plain': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
            'filters': [
                'request_id_filter',
                'service_name_filter'
            ]
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO'
        }
    }
}


class RequestIdFilter(logging.Filter):

    def filter(self, record) -> bool:
        record.request_id = getattr(
            flask.request, 'request_id', ''
        ) if flask.has_request_context() else ''
        return True


class ServiceNameFilter(Filter):

    def __init__(self, service_name: Optional[str] = None) -> None:
        super(ServiceNameFilter, self).__init__()
        self.service_name = service_name

    def filter(self, record) -> bool:
        record.service_name = self.service_name if self.service_name else 'unknown'
        return True


class JsonFormatter(Formatter):

    fmt_fields = (
        'asctime',
        'service_name',
        'process',
        'levelname',
        'lineno',
        'name',
        'request_id',
        'message'
    )

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        fmt: Optional[Sequence] = None,
        datefmt: Optional[str] = None
    ) -> None:

        if fmt and not isinstance(fmt, (tuple, list)):
            raise TypeError(f'fmt param must be tuple or list type, current type: {type(fmt)}')
        self._fmt: Sequence = fmt or self.fmt_fields  # type: ignore[assignment]

        self.datefmt = datefmt

    def _get_exception_text(self, record) -> str:
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        result = f'{record.exc_text}' if record.exc_text else ''
        return result

    def usesTime(self) -> bool:
        """
        Check if the format uses the creation time of the record.
        """
        return 'asctime' in self._fmt

    def format(self, record: LogRecord) -> str:
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        result = OrderedDict()
        for field in self._fmt:
            result[field] = record.__dict__.get(field, '')

        if record.exc_info:
            result['exc'] = self._get_exception_text(record)

        return json.dumps(result)

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
        ct = datetime.datetime.fromtimestamp(record.created, tzlocal.get_localzone())
        if datefmt:
            result = ct.strftime(datefmt)
        else:
            time_zone = ct.strftime('%z')
            time_zone = time_zone[:-2] + ':' + time_zone[-2:]
            time_str = ct.strftime('%Y-%m-%dT%H:%M:%S')
            result = "%s.%03d%s" % (time_str, record.msecs, time_zone)
        return result


def config_logging(service_name: Optional[str] = None, debug: bool = False):
    """
    Config logging of a service

    Args:
        service_name (str): recommend providing a service name to distinguish source
        debug (bool): When true, logger would use plain log format
    """
    dict_config = copy.deepcopy(DEFAULT_LOG_CONFIG_DICT)
    if service_name:
        dict_config['filters']['service_name_filter']['service_name'] = service_name  # type: ignore[index]
    if debug:
        dict_config['loggers']['']['handlers'] = ['plain']  # type: ignore[index]
    dictConfig(dict_config)


class LoggingMiddleware(object):

    # pylint: disable=no-self-use
    def before_request(self):
        environ = request.environ
        access_vars = {
            'remote_addr': environ.get('REMOTE_ADDR', '-'),
            'request_method': environ.get('REQUEST_METHOD'),
            'path': environ.get('PATH_INFO'),
            'query_string': environ.get('QUERY_STRING'),
        }
        access_str = '%(remote_addr)s, %(request_method)s, %(path)s, %(query_string)s' % access_vars
        logger.info('Before request: %s', access_str, extra={'tags': access_vars})

    # pylint: disable=no-self-use
    def after_request(self, resp: ResponseClass):
        environ = request.environ
        status = resp.status
        if isinstance(status, str):
            status = status.split(None, 1)[0]
        response_vars = {'status': status}

        try:
            status_val = int(status)
        except ValueError:
            pass
        else:
            if status_val >= 500 and status_val != 501:
                req_method = environ.get('REQUEST_METHOD')
                if req_method and req_method.lower() == 'post':
                    response_vars['body'] = request.get_json()

        response_str = '%(status)s' % response_vars
        logger.info('After request: %s', response_str, extra={'tags': response_vars})
        return resp

    @classmethod
    def install(cls, app: Flask, service_name: str, debug=False):
        config_logging(service_name, debug)
        mw = cls()
        app.before_request(mw.before_request)
        app.after_request(mw.after_request)
