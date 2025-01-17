"""
Utilities on electricity usage data with monthly granularity
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
    SGCC_XPATH_USAGE_HIST_MONTHLY_DETAILED_TBODY,
    SGCC_XPATH_USAGE_HIST_MONTHLY_TAB_DIV,
    SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN,
    SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN_BUTTON,
    SGCC_XPATH_USAGE_HIST_RESIDENT_ID_SPAN,
    SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN,
    SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON,
    SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN,
    SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN_BUTTON
)
from ....exceptions import LoadTableTimeoutError
from ....schemes import Usage


logger = logging.getLogger(__name__)


__all__ = ['get_monthly_usage_history']


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def get_monthly_usage_history(page: Page) -> List[Usage]:
    """
    get monthly usage and charge for each bound resident
    within recent 3 years
    """
    logger.info('start to get monthly usage data')
    page.goto(url=SGCC_WEB_URL_USAGE_HIST, timeout=SGCC_TIMEOUT)

    resident_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN}'
    )
    avail_resident_amounts = len(resident_options)

    year_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN}'
    )
    avail_year_amounts = len(year_options)

    result: List[Usage] = []
    for resident_idx in range(avail_resident_amounts):
        for year_idx in range(avail_year_amounts):
            logger.info(
                f'try to get '
                f'{resident_idx + 1}{get_ordinal_suffix(resident_idx + 1)} resident of '
                f'{year_idx + 1}{get_ordinal_suffix(year_idx + 1)} year\'s '
                f'monthly usage data'
            )
            try:
                usages = _get_single_resident_monthly_usage_history(
                    page,
                    resident_idx,
                    year_idx
                )
                result.extend(usages)
            except LoadTableTimeoutError:
                logger.warning(
                    f'No available monthly usage data for '
                    f'{resident_idx + 1}{get_ordinal_suffix(resident_idx + 1)} resident in '
                    f'{year_idx + 1}{get_ordinal_suffix(year_idx + 1)} year'
                )

    logger.info('get monthly usage data succeed')
    return result


@retry(
    retry_limit=SGCC_RETRY_LIMIT,
    exceptions=(TimeoutError,)
)
def _get_single_resident_monthly_usage_history(
    page: Page,
    resident_idx: int,
    year_idx: int
) -> List[Usage]:
    """
    get monthly usage of single resident
    1. view the page
    2. click given resident option
    3. click tab for monthly data
    4. click given year option
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

    monthly_tab_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_MONTHLY_TAB_DIV}'
    )
    load_locator(monthly_tab_locator)
    monthly_tab_locator.click()
    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

    year_options = get_sgcc_dropdown_lis(
        page,
        f'xpath={SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN_BUTTON}',
        f'xpath={SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN}'
    )
    avail_year_amounts = len(year_options)
    if year_idx > avail_year_amounts - 1:
        raise ValueError(
            ERR_MSG_TML_OVERFLOW.format(
                serial=f'{year_idx + 1}{get_ordinal_suffix(year_idx + 1)}',
                entity_name='Year',
                amount=avail_year_amounts
            )
        )
    year_option = year_options[year_idx]
    year_option.click()
    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

    resident_id_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_RESIDENT_ID_SPAN}'
    )
    load_locator(resident_id_locator)
    resident_id = int(resident_id_locator.inner_text().strip())

    tbody_locator = page.locator(
        f'xpath={SGCC_XPATH_USAGE_HIST_MONTHLY_DETAILED_TBODY}'
    )
    try:
        load_locator(tbody_locator)
    except TimeoutError:
        raise LoadTableTimeoutError()
    tr_locator = tbody_locator.locator('> tr')

    data: List[Usage] = []
    for tr_dom in tr_locator.element_handles():
        date_range_td, usage_td, charge_td = tr_dom.query_selector_all('td')

        start_date_string, end_date_string = map(
            lambda item: item.inner_text().strip(),
            date_range_td.query_selector_all('> div > span > span')
        )
        start_date_string = start_date_string[: -1]  # remove dash suffix
        start_date = datetime.datetime.strptime(
            start_date_string,
            DATE_FORMAT
        ).date()
        if start_date.day != 1:
            logger.warning((
                f'The monthly usage history data is monthly-partial '
                f'which would be skipped: {start_date_string} ~ {end_date_string}'
            ))
            continue

        elec_usage_span = usage_td.query_selector('div > span')
        elec_usage = None
        if elec_usage_span:
            elec_usage = float(elec_usage_span.inner_text().strip())

        elec_charge_span = charge_td.query_selector('div > span')
        elec_charge = None
        if elec_charge_span:
            elec_charge = float(elec_charge_span.inner_text().strip())

        record: Usage = {
            'resident_id': resident_id,
            'date': start_date,
            'granularity': DateGranularity.MONTHLY.value,
            'elec_usage': elec_usage,
            'elec_charge': elec_charge
        }
        data.append(record)

    return data
