"""
Task implementation
"""
import logging
import os
import signal
import sys
import threading
import time
from types import FrameType
from typing import Optional

from playwright.sync_api import sync_playwright
import schedule

from .conf import settings
from .core.services.acquisition_service import AcquisitionService
from .databases import prepare_models
from .core.utils.load import (
    load_balances,
    load_residents,
    load_usages
)
from .log import config_logging


logger = logging.getLogger(__name__)


def collect_sgcc_data() -> None:
    """
    collect data by headless browser,
    loading into database
    """
    try:
        _collect_sgcc_data()
    except Exception as e:
        logger.exception(e)
        raise


def _collect_sgcc_data() -> None:
    """
    collect data by headless browser,
    loading into database
    """
    logger.info('start to collect SGCC data')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        service = AcquisitionService(
            settings.SGCC_ACCOUNT_USERNAME,
            settings.SGCC_ACCOUNT_PASSWORD,
            browser
        )
        residents = service.get_residents()
        balance = service.get_balance()
        daily_usage = service.get_daily_usage_history()
        monthly_usage = service.get_monthly_usage_history()

    prepare_models()
    load_residents(residents)
    load_balances(balance)
    load_usages(daily_usage + monthly_usage)
    logger.info('collect SGCC data successfully')


def run() -> None:
    config_logging('sgcc-alert-periodic', settings.DEBUG)

    def _exit(signal_number: int, _frame: Optional[FrameType]) -> None:
        logger.warning(
            f'App exits since signal {signal_number} received in process PID {os.getpid()}'
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, _exit)
    signal.signal(signal.SIGTERM, _exit)

    _schedule_tasks()

    if settings.SYNC_INITIALIZED:
        logger.info('job triggered as initialization')
        init_thread = threading.Thread(target=collect_sgcc_data)
        init_thread.daemon = True
        init_thread.start()

    thread = threading.Thread(target=_poll_tasks)
    thread.daemon = True
    thread.start()


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


def _serial_run_tasks() -> None:
    jobs = schedule.get_jobs()
    for job in jobs:
        job.run()
