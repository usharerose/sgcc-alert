"""
Utilities on resident balance
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
    DATETIME_FORMAT,
    ERR_MSG_TML_OVERFLOW,
    SGCC_RETRY_LIMIT,
    SGCC_TIMEOUT,
    SGCC_TIMEOUT_LOAD_PAGE,
    SGCC_WEB_URL_BALANCE,
    SGCC_XPATH_BALANCE_DETAILED_DIV,
    SGCC_XPATH_BALANCE_RESIDENT_ID_SPAN,
    SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_BUTTON,
    SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_MENU
)
from ....schemes import Balance


logger = logging.getLogger(__name__)


__all__ = ['get_balance']


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def get_balance(page: Page) -> List[Balance]:
    """
    get current balance of each bound resident
    """
    logger.info('start to get balance data')
    page.goto(url=SGCC_WEB_URL_BALANCE, timeout=SGCC_TIMEOUT)

    resident_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_MENU}'
    )
    avail_resident_amounts = len(resident_options)

    result: List[Balance] = []
    for idx in range(avail_resident_amounts):
        logger.info(
            f'try to get {idx + 1}{get_ordinal_suffix(idx + 1)} resident balance data'
        )
        data = _get_single_resident_balance(page, idx)
        result.append(data)

    logger.info('get balance data succeed')
    return result


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def _get_single_resident_balance(
    page: Page,
    resident_idx: int
) -> Balance:
    """
    get current balance of single resident
    1. view the page
    2. click given resident option
    3. parse Web page for the identifier of selected resident
    4. parse Web page for detailed data about
       * data time
       * balance value and estimate remain days
    """
    page.goto(url=SGCC_WEB_URL_BALANCE, timeout=SGCC_TIMEOUT)

    resident_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_MENU}'
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

    resident_id_locator = page.locator(
        f'xpath={SGCC_XPATH_BALANCE_RESIDENT_ID_SPAN}'
    )
    load_locator(resident_id_locator)
    resident_id = int(resident_id_locator.inner_text().strip())

    detailed_div_locator = page.locator(
        f'xpath={SGCC_XPATH_BALANCE_DETAILED_DIV}'
    )
    load_locator(detailed_div_locator)
    date_div_dom, balance_div_dom = detailed_div_locator.locator(
        '> div'
    ).element_handles()

    _, date_span_dom = date_div_dom.query_selector_all('> span')
    datetime_string = date_span_dom.inner_text().strip()
    ordinal_date = datetime.datetime.strptime(
        datetime_string,
        DATETIME_FORMAT
    ).toordinal()

    balance_div_dom, est_remain_days_div_dom = balance_div_dom.query_selector_all('> div')

    _, balance_span_dom, _ = balance_div_dom.query_selector_all('> span')
    balance = float(balance_span_dom.inner_text())

    _, est_remain_days_span_dom, _ = est_remain_days_div_dom.query_selector_all('> span')
    est_remain_days = int(est_remain_days_span_dom.inner_text())

    record: Balance = {
        'resident_id': resident_id,
        'date': ordinal_date,
        'granularity': DateGranularity.DAILY.value,
        'balance': balance,
        'est_remain_days': est_remain_days
    }

    return record
