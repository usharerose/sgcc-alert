"""
Application
"""
import logging
from typing import Dict

from flask import Flask, request

from .conf import settings
from .core.services.query_service import QueryService
from .databases.session import prepare_models
from .log import LoggingMiddleware
from .routes import API_V1
from .tracing import TracingMiddleware


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    _app = Flask(__name__)
    TracingMiddleware.install(_app)
    LoggingMiddleware.install(_app, 'sgcc-alert', settings.DEBUG)
    prepare_models()
    return _app


app = create_app()


app.register_blueprint(API_V1, url_prefix='/api/v1.0')


@app.route('/', methods=['GET'])
def index() -> Dict:
    return {
        'data': 'This is SGCC Alert'
    }


@app.route('/get-resident', methods=['POST'])
def get_resident():
    payload = request.json or {}

    return QueryService.query_resident(
        payload.get('resident_id'),
        payload.get('exclude_non_main_resident'),
        payload.get('order_by'),
        payload.get('pagination')
    )


@app.route('/get-latest-balance', methods=['GET'])
def get_latest_balance():
    resident_id = request.args.get('resident_id')

    result = QueryService.query_latest_balance(int(resident_id))
    return {
        'data': result
    }


if __name__ == '__main__':
    app.run()
