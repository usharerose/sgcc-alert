"""
Application
"""
from .conf import settings
from .log import config_logging
from .tasks import collect_sgcc_data


def run() -> None:
    collect_sgcc_data()


if __name__ == '__main__':
    config_logging('sgcc-alert', settings.DEBUG)
    run()
