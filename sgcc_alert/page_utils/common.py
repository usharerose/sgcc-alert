"""
Common utilities
"""
import logging
from typing import List, Optional, Literal

from playwright.sync_api import Locator, Page
from playwright.sync_api._generated import ElementHandle
from playwright._impl._errors import TimeoutError

from ..constants import (
    SGCC_PAGE_VISITING_INTERVAL,
    SGCC_LOAD_DOM_RETRY_LIMIT,
    SGCC_TIMEOUT_LOAD_PAGE
)
from ..common import retry


logger = logging.getLogger(__name__)


def get_sgcc_dropdown_lis(
    page: Page,
    button_selector: str,
    dropdown_selector: str
) -> List[ElementHandle]:
    """
    get DOM elements of dropdown options
    :param page: SGCC web page
    :type page: playwright.sync_api.Page
    :param button_selector: A selector to use when resolving related button DOM element
    :type button_selector: str
    :param dropdown_selector: A selector to use when resolving related dropdown DOM element
    :type dropdown_selector: str
    :return: List[ElementHandle]
    """
    button_locator = page.locator(button_selector)
    load_locator(button_locator)
    button_locator.click()
    page.wait_for_timeout(SGCC_PAGE_VISITING_INTERVAL)

    dropdown_locator = page.locator(dropdown_selector)
    load_locator(dropdown_locator)
    list_item_locator = dropdown_locator.locator('li')
    return [item for item in list_item_locator.element_handles()]


@retry(
    retry_limit=SGCC_LOAD_DOM_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def load_locator(
    locator: Locator,
    state: Optional[
        Literal['attached', 'detached', 'hidden', 'visible']
    ] = 'visible',
    timeout: Optional[float] = SGCC_TIMEOUT_LOAD_PAGE
) -> None:
    locator.wait_for(state=state, timeout=timeout)
