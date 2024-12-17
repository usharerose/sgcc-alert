"""
Application
"""
import logging
from typing import Dict

from flask import Flask

from .conf import settings
from .log import LoggingMiddleware
from .tracing import TracingMiddleware


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    _app = Flask(__name__)
    TracingMiddleware.install(_app)
    LoggingMiddleware.install(_app, 'sgcc-alert', settings.DEBUG)
    return _app


app = create_app()


@app.route('/', methods=['GET'])
def index() -> Dict:
    return {
        'data': 'This is SGCC Alert'
    }


if __name__ == '__main__':
    app.run()
