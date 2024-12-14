"""
Utilities on electricity usage data with daily granularity
"""
import datetime
import logging
from typing import List

from playwright.sync_api import Page
from playwright._impl._errors import TimeoutError

from .common import get_sgcc_dropdown_lis, load_locator
from ..common import get_ordinal_suffix, retry
from ....constants import (
    DateGranularity,
    DATE_FORMAT,
    ERR_MSG_TML_OVERFLOW,
    SGCC_RETRY_LIMIT,
    SGCC_TIMEOUT,
    SGCC_TIMEOUT_LOAD_PAGE,
    SGCC_WEB_URL_USAGE_HIST,
    SGCC_XPATH_USAGE_HIST_DAILY_DETAILED_TBODY,
    SGCC_XPATH_USAGE_HIST_DAILY_RECENT_THIRTY_DAYS_CHECKBOX_SPAN,
    SGCC_XPATH_USAGE_HIST_DAILY_TAB_DIV,
    SGCC_XPATH_USAGE_HIST_RESIDENT_ID_SPAN,
    SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN,
    SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON
)
from ....exceptions import LoadTableTimeoutError
from ....schemes import Usage


logger = logging.getLogger(__name__)


__all__ = ['get_daily_usage_history']


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def get_daily_usage_history(page: Page) -> List[Usage]:
    """
    get daily usage for each bound resident
    within recent 30 days
    """
    logger.info('start to get daily usage data')
    page.goto(url=SGCC_WEB_URL_USAGE_HIST, timeout=SGCC_TIMEOUT)

    resident_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN}'
    )
    avail_resident_amounts = len(resident_options)

    result: List[Usage] = []
    for idx in range(avail_resident_amounts):
        logger.info(
            f'try to get {idx + 1}{get_ordinal_suffix(idx + 1)} '
            f'resident daily usage data'
        )
        try:
            usages = _get_single_resident_daily_usage_history(
                page,
                idx
            )
            result.extend(usages)
        except LoadTableTimeoutError:
            logger.warning(
                f'No available daily usage data '
                f'for {idx + 1}{get_ordinal_suffix(idx + 1)} resident'
            )

    logger.info('get daily usage data succeed')
    return result


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(LoadTableTimeoutError, TimeoutError)
)
def _get_single_resident_daily_usage_history(
    page: Page,
    resident_idx: int
) -> List[Usage]:
    """
    get daily usage of single resident
    1. view the page
    2. click given resident option
    3. click tab for daily data
    4. click checkbox for recent 30 days data
    5. parse Web page for the identifier of selected resident
    6. parse Web page for detailed data in the table
    """
    page.goto(url=SGCC_WEB_URL_USAGE_HIST, timeout=SGCC_TIMEOUT)

    resident_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN}'
    )
    avail_resident_amounts = len(resident_options)
    if resident_idx > avail_resident_amounts - 1:
        raise ValueError(
            ERR_MSG_TML_OVERFLOW.format(
                serial=f'{resident_idx + 1}{get_ordinal_suffix(resident_idx + 1)}',
                entity_name='Resident',
                amount=avail_resident_amounts
            )
        )
    resident_option = resident_options[resident_idx]
    resident_option.click()
    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

    daily_tab_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_DAILY_TAB_DIV}'
    )
    load_locator(daily_tab_locator)
    daily_tab_locator.click()
    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

    recent_thirty_days_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_DAILY_RECENT_THIRTY_DAYS_CHECKBOX_SPAN}'
    )
    load_locator(recent_thirty_days_locator)
    recent_thirty_days_locator.click()
    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

    resident_id_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENT_ID_SPAN}'
    )
    load_locator(resident_id_locator)
    resident_id = int(resident_id_locator.inner_text().strip())

    tbody_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_DAILY_DETAILED_TBODY}'
    )
    try:
        load_locator(tbody_locator)
    except TimeoutError:
        raise LoadTableTimeoutError()
    tr_locator = tbody_locator.locator('> tr')

    data: List[Usage] = []
    for tr_dom in tr_locator.element_handles():
        date_td, usage_td, _ = tr_dom.query_selector_all('td')

        date_cell_div = date_td.query_selector('div')
        assert date_cell_div is not None
        date_string = date_cell_div.inner_text().strip()
        ordinal_date = datetime.datetime.strptime(date_string, DATE_FORMAT).toordinal()

        elec_usage_div = usage_td.query_selector('div')
        elec_usage = None
        if elec_usage_div:
            elec_usage = float(elec_usage_div.inner_text().strip())

        record: Usage = {
            'resident_id': resident_id,
            'date': ordinal_date,
            'granularity': DateGranularity.DAILY.value,
            'elec_usage': elec_usage,
            'elec_charge': None  # There is no charge data in daily history
        }
        data.append(record)

    return data
