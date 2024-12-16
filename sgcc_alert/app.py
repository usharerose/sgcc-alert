"""
Application
"""
import logging
import os
import signal
import sys
import threading
import time
from types import FrameType
from typing import Optional

import schedule

from .conf import settings
from .log import config_logging
from .tasks import collect_sgcc_data


logger = logging.getLogger(__name__)


def run() -> None:

    def _exit(signal_number: int, _frame: Optional[FrameType]) -> None:
        logger.warning(
            f'App exits since signal {signal_number} received in process PID {os.getpid()}'
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, _exit)
    signal.signal(signal.SIGTERM, _exit)

    _schedule_tasks()

    logger.info('start to run all jobs as initialization')
    jobs = schedule.get_jobs()
    for job in jobs:
        job.run()
    logger.info('finish running all jobs as initialization')

    thread = threading.Thread(target=_poll_tasks)
    thread.daemon = True
    thread.start()

    # 保持主线程常驻
    while True:
        time.sleep(10)


def _schedule_tasks() -> None:
    schedule.every().day.at(settings.DAILY_CRON_TIME).do(collect_sgcc_data)


def _poll_tasks() -> None:
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.exception(e)
        finally:
            time.sleep(settings.POLL_INTERVAL)


if __name__ == '__main__':
    config_logging('sgcc-alert', settings.DEBUG)
    run()
