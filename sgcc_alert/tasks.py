"""
Task implementation
"""
from playwright.sync_api import sync_playwright

from .conf import settings
from .core.services.acquisition_service import AcquisitionService
from .databases import prepare_models
from .core.utils.load import (
    load_balances,
    load_residents,
    load_usages
)


def collect_sgcc_data():
    """
    collect data by headless browser,
    loading into database
    """
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
