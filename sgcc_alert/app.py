"""
Application
"""
import logging

import connexion
from flask import Flask

from .conf import settings
from .databases.session import prepare_models
from .log import LoggingMiddleware
from .tracing import TracingMiddleware


logger = logging.getLogger(__name__)


def create_app() -> Flask:
    _app = connexion.App(
        __name__,
        specification_dir="./docs",
        options={
            "swagger_ui": True,
            "swagger_url": "/docs"
        }
    )

    _app.add_api("swagger.yml", base_path='/api/v1.0')

    TracingMiddleware.install(_app.app)
    LoggingMiddleware.install(_app.app, 'sgcc-alert', settings.DEBUG)

    prepare_models()

    return _app.app


app = create_app()


if __name__ == '__main__':
    app.run()
