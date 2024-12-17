from typing import Any

from sgcc_alert.tasks import run


bind = "0.0.0.0:8000"
workers = 4
worker_class = 'sync'
graceful_timeout = 30


def on_starting(server: Any):
    run()
