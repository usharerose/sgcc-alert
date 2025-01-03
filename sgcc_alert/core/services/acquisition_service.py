"""
Service for SGCC data acquisition from web page
"""
from typing import List

from playwright.sync_api import Browser

from .login_service import SGCCLoginService
from ..utils.page_action import (
    get_balance as _get_balance,
    get_daily_usage_history as _get_daily_usage_history,
    get_monthly_usage_history as _get_monthly_usage_history,
    get_residents as _get_residents,
)
from ...schemes import Balance, Resident, Usage


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
        login_service = SGCCLoginService(self._username, self._password, self._page)
        login_service.login()

    def get_residents(self) -> List[Resident]:
        """
        get the bound residents of login account
        """
        return _get_residents(self._page)

    def get_balance(self) -> List[Balance]:
        """
        get current balance of each bound resident
        """
        return _get_balance(self._page)

    def get_daily_usage_history(self) -> List[Usage]:
        """
        get daily usage for each bound resident
        within recent 30 days
        """
        return _get_daily_usage_history(self._page)

    def get_monthly_usage_history(self) -> List[Usage]:
        """
        get monthly usage and charge for each bound resident
        within recent 3 years
        """
        return _get_monthly_usage_history(self._page)
