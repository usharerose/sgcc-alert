"""
Service for SGCC data acquisition from web page
"""
from typing import List

from playwright.sync_api import Browser

from .schemes import Balance, Resident, Usage
from .page_utils import (
    get_balance as get_balance_util,
    get_daily_usage_history as get_daily_usage_history_util,
    get_monthly_usage_history as get_monthly_usage_history_util,
    get_residents as get_residents_util,
    login as login_util
)


class AcquisitionService:

    def __init__(
        self,
        username: str,
        password: str,
        browser: Browser
    ) -> None:
        self._username = username
        self._password = password
        self._page = browser.new_page()
        self._login()

    def _login(self) -> None:
        login_util(self._page, self._username, self._password)

    def get_residents(self) -> List[Resident]:
        return get_residents_util(self._page)

    def get_balance(self) -> List[Balance]:
        return get_balance_util(self._page)

    def get_daily_usage_history(self) -> List[Usage]:
        return get_daily_usage_history_util(self._page)

    def get_monthly_usage_history(self) -> List[Usage]:
        return get_monthly_usage_history_util(self._page)
