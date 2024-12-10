"""
Utilities on resident list
"""
import logging
from typing import List

from playwright.sync_api import Page
from playwright.sync_api._generated import ElementHandle  # NOQA
from playwright._impl._errors import TimeoutError  # NOQA

from ..constants import (
    SGCC_TIMEOUT,
    SGCC_WEB_URL_DOOR_NUMBER_MANAGER,
    SGCC_XPATH_DOORNUM_MANAGER_DETAILED_DIV
)
from ..exceptions import LoadResidentInfoError
from ..schemes import Resident


logger = logging.getLogger(__name__)


__all__ = ['get_residents']


def get_residents(page: Page) -> List[Resident]:
    """
    get the bound residents of login account
    """
    page.goto(url=SGCC_WEB_URL_DOOR_NUMBER_MANAGER, timeout=SGCC_TIMEOUT)

    door_info_div_locator = page.locator(
        f'xpath={SGCC_XPATH_DOORNUM_MANAGER_DETAILED_DIV}'
    )
    door_info_div_locator.wait_for(state='attached', timeout=SGCC_TIMEOUT)

    result: List[Resident] = []
    for section_dom in door_info_div_locator.locator('section').element_handles():
        item = _parse_resident_section(section_dom)
        result.append(item)

    return result


def _parse_resident_section(section_dom: ElementHandle) -> Resident:
    developer_span_dom: ElementHandle
    is_main_door_span_dom: ElementHandle
    resident_info_div_dom: ElementHandle
    resident_id_paragraph_dom: ElementHandle
    resident_addr_paragraph_dom: ElementHandle

    developer_span_dom, is_main_door_span_dom, _ = section_dom.query_selector_all(
        '.title-info span'
    )

    developer_name = developer_span_dom.inner_text().strip()

    is_main = True
    is_main_door_span_class_name = is_main_door_span_dom.get_attribute('class')
    if is_main_door_span_class_name == 'set-main-door':
        is_main = False

    resident_info_div_dom, *_ = section_dom.query_selector_all('.main-info div')
    resident_id_paragraph_dom, resident_addr_paragraph_dom = resident_info_div_dom.query_selector_all('p')

    resident_id_string = resident_id_paragraph_dom.get_attribute('title')
    if resident_id_string is None:
        raise LoadResidentInfoError()
    resident_id = int(resident_id_string.strip())

    resident_address = resident_addr_paragraph_dom.get_attribute('title')
    if resident_address is not None:
        resident_address = resident_address.strip()

    data: Resident = {
        'resident_id': resident_id,
        'is_main': is_main,
        'resident_address': resident_address,
        'developer_name': developer_name
    }

    return data
