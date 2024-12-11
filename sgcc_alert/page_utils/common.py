"""
Common utilities
"""
from typing import List

from playwright.sync_api import Page
from playwright.sync_api._generated import ElementHandle

from ..constants import SGCC_TIMEOUT


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
    button_locator.wait_for(state='visible', timeout=SGCC_TIMEOUT)
    button_locator.click()

    dropdown_locator = page.locator(dropdown_selector)
    dropdown_locator.wait_for(state='visible', timeout=SGCC_TIMEOUT)
    list_item_locator = dropdown_locator.locator('li')
    return [item for item in list_item_locator.element_handles()]


def get_ordinal_suffix(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return 'th'
    units_digit = value % 10
    if units_digit == 1:
        return 'st'
    if units_digit == 2:
        return 'nd'
    if units_digit == 3:
        return 'rd'
    return 'th'
