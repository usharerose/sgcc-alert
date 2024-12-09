"""
Service for SGCC web page manipulation
"""
from collections import OrderedDict
import datetime
import logging
import random
import time
from typing import List, Optional, Tuple, TypedDict

from playwright.sync_api import Page
from playwright.sync_api._generated import ElementHandle  # NOQA

from .notch_service import NotchService


logger = logging.getLogger(__name__)


TIMEOUT = 5 * 1000  # millisecond
WEB_URL_LOGIN = 'https://www.95598.cn/osgweb/login'
WEB_URL_MY_ACCOUNT = 'https://www.95598.cn/osgweb/my95598'
WEB_URL_DOOR_NUMBER_MANAGER = 'https://www.95598.cn/osgweb/doorNumberManeger'
WEB_URL_BALANCE_QUERY = 'https://www.95598.cn/osgweb/userAcc'


XPATH_LOGIN_BY_ACCOUNT = '//*[@id="login_box"]/div[1]/div[3]'
XPATH_ACCOUNT_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[1]/div/div/input'
XPATH_PASSWORD_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[2]/div/div/input'
XPATH_AGREE_TOS_CHECKBOX = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[3]/div/span[2]'
XPATH_LOGIN_BUTTON = '//*[@id="login_box"]/div[2]/div[1]/form/div[2]/div/button'
XPATH_MY_ACCOUNT_RESIDENTS_DROP_DOWN_BUTTON = '//*[@id="member_info"]/div/div/div/div/div[2]/ul/li[3]/div'
XPATH_MY_ACCOUNT_RESIDENTS_DROP_DOWN_MENU = '/html/body/ul'
XPATH_DOOR_NUM_MANAGER_DOOR_INFO_DIV = (
    'xpath=/html/body/div/div/div/article/div/div/div[2]/div/div/div[1]/div[2]'
    '/div/div/div/div[2]/div[1]/div/div[1]/div/div[1]/div[2]/div/div/div'
)
XPATH_BALANCE_RESIDENTS_DROP_DOWN_BUTTON = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div/div[1]/div[2]'
    '/div/div/div/div[2]/div/div[1]/div/ul/li/div[2]/div[1]/span/span/i'
)
XPATH_BALANCE_RESIDENTS_DROP_DOWN_MENU = '/html/body/div[2]/div[1]/div[1]/ul'
XPATH_BALANCE_RESIDENT_NUM_SPAN = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div/div[1]'
    '/div[2]/div/div/div/div[2]/div/div[1]/div/ul/div/li[1]/span[2]'
)
XPATH_BALANCE_DATA_DIV = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div'
    '/div[1]/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div'
)
XPATH_CAPTCHA_SLIDE_BUTTON = '//*[@id="slideVerify"]/div[2]/div/div'
XPATH_CAPTCHA_REFRESH_BUTTON = '//*[@id="slideVerify"]/div[1]'
CLASS_LOGIN_ERR_TIPS = 'errmsg-tip'
SCRIPT_TPL_IMG_ENCODE = '''
    () => {{
      const bgImgCanvas = document.querySelector('{selector}');
      if (bgImgCanvas) {{
        return bgImgCanvas.toDataURL('image/png');
      }}
      return null;
    }}
'''
SELECTOR_CAPTCHA_BG_IMG = '#slideVerify > canvas:nth-child(1)'
SELECTOR_CAPTCHA_BLOCK_IMG = '#slideVerify > canvas.slide-verify-block'


ERR_MSG_WRONG_ACCOUNT_PWD = '账号或密码错误，如连续错误5次，账号将被锁定20分钟，20分钟后自动解锁。'
ERR_MSG_REACH_LOGIN_LIMIT = '网络连接超时（RK001）,请重试！'
ERR_MSG_CAPTCHA_WRONG = '验证错误！'
ERR_MSG_LOAD_RESIDENTS_FAILED = 'Load resident info from /osgweb/doorNumberManeger failed'
ERR_MSG_TML_RESIDENT_OVERFLOW = (
    'Index of requested resident <{idx}> is overflowed than the available capacity <{amount}>'
)


DRAG_SLIDE_SPEED_UP_RATIO = 0.8
DRAG_SLIDE_SPEED_UP_ACCELERATION = 10.0
DRAG_SLIDE_TIME_STEP = 0.1
SLIDE_X_OFFSET_FACTOR = 1.05


REFRESH_CAPTCHA_RETRY_LIMIT = 5
REFRESH_RESIDENT_INFO_RETRY_LIMIT = 10


class LoginError(Exception):

    pass


class CaptchaValidationError(LoginError):

    pass


class LoginRateLimitError(LoginError):

    pass


class LoginAccountPasswordError(LoginError):

    pass


class LoadResidentInfoError(Exception):

    pass


class ResidentOverflowError(Exception):

    pass


class ResidentItem(TypedDict):

    resident_id: int
    developer_name: str


class ResidentInfoItem(TypedDict):

    resident_id: int
    is_main_resident: bool
    resident_address: str
    developer_name: str


class BalanceInfo(TypedDict):

    ordinal_date: int
    balance: float
    estimate_remain_days: float


class BalanceInfoWithResidentID(BalanceInfo):

    resident_id: int


class WebPageService:

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def login(self, page: Page) -> None:
        page.goto(url=WEB_URL_LOGIN, timeout=TIMEOUT)

        # click for login by account/password or message authentication code
        page.click(f'xpath={XPATH_LOGIN_BY_ACCOUNT}', timeout=TIMEOUT)

        # fill account and password
        page.fill(f'xpath={XPATH_ACCOUNT_INPUT}', self._username)
        page.fill(f'xpath={XPATH_PASSWORD_INPUT}', self._password)

        # click agree to terms of service checkbox
        tos_checkbox = page.locator(f'xpath={XPATH_AGREE_TOS_CHECKBOX}')
        tos_checkbox.wait_for(state='visible', timeout=TIMEOUT)
        tos_checkbox.click()
        page.click(f'xpath={XPATH_LOGIN_BUTTON}', timeout=TIMEOUT)
        # captcha image loading costs much more time
        page.wait_for_timeout(TIMEOUT)

        self._verify_slide_captcha_with_retry(page)

    def _verify_slide_captcha_with_retry(self, page: Page) -> None:
        retries = 0
        while True:
            try:
                self._verify_slide_captcha(page)
            except CaptchaValidationError:
                if retries < REFRESH_CAPTCHA_RETRY_LIMIT:
                    time.sleep(1)
                    retries += 1
                else:
                    break
            except (LoginRateLimitError, LoginAccountPasswordError, LoginError):
                raise
            else:
                break

    def _verify_slide_captcha(self, page: Page) -> None:
        x_ordinate, _ = self._recognize_notch_ordinate(page)

        # when x_ordinate is equal to 0, it means no effective recognization
        retries = 0
        while x_ordinate == 0 and retries < REFRESH_CAPTCHA_RETRY_LIMIT:
            self._refresh_captcha(page)
            x_ordinate, _ = self._recognize_notch_ordinate(page)
            retries += 1

        # raise without attempt to save daily login times limit
        if x_ordinate == 0:
            raise CaptchaValidationError(ERR_MSG_CAPTCHA_WRONG)

        # the factor on x_offset is from experience
        # which makes the slide block being in place
        self._slide_block(page, x_ordinate * SLIDE_X_OFFSET_FACTOR)

        err_tip_div = page.locator(f'.{CLASS_LOGIN_ERR_TIPS}')
        if err_tip_div.is_visible():
            err_msg = err_tip_div.locator('span').text_content()
            if err_msg == ERR_MSG_REACH_LOGIN_LIMIT:
                raise LoginRateLimitError(f'Login rate limit error: {ERR_MSG_REACH_LOGIN_LIMIT}')
            if err_msg == ERR_MSG_CAPTCHA_WRONG:
                raise CaptchaValidationError(ERR_MSG_CAPTCHA_WRONG)
            if err_msg == ERR_MSG_WRONG_ACCOUNT_PWD:
                raise LoginAccountPasswordError(ERR_MSG_WRONG_ACCOUNT_PWD)
            raise LoginError(f'Login failed: {LoginError}')
        if page.url == WEB_URL_LOGIN:
            raise LoginError('Login failed with unknown error')

    @staticmethod
    def _identify_slide_captcha(page: Page) -> Tuple[str, str]:
        """
        get data URL of canvas for slide captcha's
        background image and block image
        """
        bg_img_script = SCRIPT_TPL_IMG_ENCODE.format(selector=SELECTOR_CAPTCHA_BG_IMG)
        bg_img_data_url = page.evaluate(bg_img_script)

        slide_img_script = SCRIPT_TPL_IMG_ENCODE.format(selector=SELECTOR_CAPTCHA_BLOCK_IMG)
        slide_img_data_url = page.evaluate(slide_img_script)
        return bg_img_data_url, slide_img_data_url

    def _slide_block(self, page: Page, x_offset: float) -> None:
        """
        assume the page is with captcha,
        verify by slide action with the distance according to given offset
        """
        slide_button_box_x, slide_button_box_y = self._get_element_center_ordinates(
            page,
            XPATH_CAPTCHA_SLIDE_BUTTON
        )

        page.mouse.move(slide_button_box_x, slide_button_box_y)
        page.mouse.down()
        for sub_x_offset in self.simulate_horizontal_move_tracks(x_offset):
            sub_dest_x = slide_button_box_x + sub_x_offset

            # simulate the shake when slide
            sub_y_offset = random.uniform(-2, 2)
            sub_dest_y = slide_button_box_y + sub_y_offset

            page.mouse.move(sub_dest_x, sub_dest_y)
        page.mouse.up()
        page.wait_for_timeout(TIMEOUT)

    @staticmethod
    def simulate_horizontal_move_tracks(x_offset: float) -> List[float]:
        """
        build tracing point with speed up and speed down
        to imitate human-machine interaction
        """
        tracks = []
        cur_offset = 0.0
        # move getting slow down near the end of the distance
        mid = x_offset * DRAG_SLIDE_SPEED_UP_RATIO
        velocity = 0.0
        while cur_offset < x_offset:
            acceleration: float = DRAG_SLIDE_SPEED_UP_ACCELERATION  # speed up
            if cur_offset >= mid:
                acceleration = (
                    -1 * DRAG_SLIDE_SPEED_UP_ACCELERATION * DRAG_SLIDE_SPEED_UP_RATIO /
                    (1 - DRAG_SLIDE_SPEED_UP_RATIO)
                )  # speed down at the second half
            span = velocity * DRAG_SLIDE_TIME_STEP + 0.5 * acceleration * DRAG_SLIDE_TIME_STEP ** 2
            velocity = velocity + acceleration * DRAG_SLIDE_TIME_STEP
            cur_offset += span
            tracks.append(round(cur_offset, 4))
        return tracks

    @staticmethod
    def _get_element_center_ordinates(page: Page, x_path: str) -> Tuple[float, float]:
        element = page.locator(f'xpath={x_path}')
        element_box = element.bounding_box()
        assert element_box is not None
        x_ordinate = element_box['x'] + element_box['width'] / 2
        y_ordinate = element_box['y'] + element_box['height'] / 2
        return x_ordinate, y_ordinate

    def _refresh_captcha(self, page: Page) -> None:
        x_ordinate, y_ordinate = self._get_element_center_ordinates(
            page,
            XPATH_CAPTCHA_REFRESH_BUTTON
        )
        page.mouse.click(x_ordinate, y_ordinate)
        page.wait_for_timeout(TIMEOUT)

    def _recognize_notch_ordinate(self, page: Page) -> Tuple[int, int]:
        bg_data_url, slide_data_url = self._identify_slide_captcha(page)
        notch_service = NotchService(bg_data_url, slide_data_url)
        x_ordinate, y_ordinate = notch_service.recognize_notch()
        return x_ordinate, y_ordinate

    # deprecated
    @staticmethod
    def get_residents_from_profile(page: Page) -> List[ResidentItem]:
        """
        get the bound residents of login account
        """
        page.goto(url=WEB_URL_MY_ACCOUNT, timeout=TIMEOUT)
        drop_down_button = page.locator(f'xpath={XPATH_MY_ACCOUNT_RESIDENTS_DROP_DOWN_BUTTON}')
        drop_down_button.wait_for(state='visible', timeout=TIMEOUT)
        drop_down_button.click()
        drop_down_menu = page.locator(f'xpath={XPATH_MY_ACCOUNT_RESIDENTS_DROP_DOWN_MENU}')
        drop_down_menu.wait_for(state='visible', timeout=TIMEOUT)
        resident_list_item = drop_down_menu.locator('li')
        result = []
        for item in resident_list_item.element_handles():
            text = item.inner_text().strip()
            developer_name, resident_id_string = text.split(':')
            resident_id = int(resident_id_string)
            resident_item: ResidentItem = {
                'resident_id': resident_id,
                'developer_name': developer_name
            }
            result.append(resident_item)
        return result

    def get_residents(self, page: Page) -> Optional[List[ResidentInfoItem]]:
        retries = 0
        result: Optional[List[ResidentInfoItem]] = None
        while retries < REFRESH_RESIDENT_INFO_RETRY_LIMIT:
            try:
                result = self._get_residents(page)
                return result
            except LoadResidentInfoError:
                time.sleep(2)
                retries += 1
        return result

    @staticmethod
    def _get_residents(page: Page) -> List[ResidentInfoItem]:
        """
        get the bound residents of login account from doorNumberManager page
        """
        page.goto(url=WEB_URL_DOOR_NUMBER_MANAGER, timeout=TIMEOUT)
        door_info_div = page.locator(XPATH_DOOR_NUM_MANAGER_DOOR_INFO_DIV)
        door_info_div.wait_for(state='attached', timeout=TIMEOUT)
        sections = door_info_div.locator('section')
        result = []
        for section in sections.element_handles():
            developer_span: ElementHandle
            is_main_door_span: ElementHandle
            user_info_div: ElementHandle
            resident_id_paragraph: ElementHandle
            resident_addr_paragraph: ElementHandle

            developer_span, is_main_door_span, _ = section.query_selector_all('.title-info span')

            developer_name = developer_span.inner_text().strip()

            is_main_resident = True
            is_main_door_span_class = is_main_door_span.get_attribute('class')
            if is_main_door_span_class == 'set-main-door':
                is_main_resident = False

            user_info_div, *_ = section.query_selector_all('.main-info div')
            resident_id_paragraph, resident_addr_paragraph = user_info_div.query_selector_all('p')
            try:
                resident_id = int((resident_id_paragraph.get_attribute('title') or '').strip())
            except ValueError:
                raise LoadResidentInfoError(ERR_MSG_LOAD_RESIDENTS_FAILED)
            resident_address = (resident_addr_paragraph.get_attribute('title') or '').strip()

            resident_info_item: ResidentInfoItem = {
                'resident_id': resident_id,
                'is_main_resident': is_main_resident,
                'resident_address': resident_address,
                'developer_name': developer_name
            }
            result.append(resident_info_item)
        return result

    def get_resident_balances(self, page: Page) -> OrderedDict[int, BalanceInfo]:
        """
        get the balance of each bound resident
        """
        page.goto(url=WEB_URL_BALANCE_QUERY, timeout=TIMEOUT)
        dom_items = self._get_balance_residents_list_items(page)
        avail_resident_amounts = len(dom_items)
        result: OrderedDict[int, BalanceInfo] = OrderedDict()
        for idx in range(avail_resident_amounts):
            balance_data = self._get_resident_balance(page, idx)
            result[balance_data['resident_id']] = {
                'ordinal_date': balance_data['ordinal_date'],
                'balance': balance_data['balance'],
                'estimate_remain_days': balance_data['estimate_remain_days']
            }
        return result

    def _get_resident_balance(self, page: Page, selection_idx: int) -> BalanceInfoWithResidentID:
        page.goto(url=WEB_URL_BALANCE_QUERY, timeout=TIMEOUT)
        dom_items = self._get_balance_residents_list_items(page)
        if selection_idx > len(dom_items) - 1:
            raise ResidentOverflowError(
                ERR_MSG_TML_RESIDENT_OVERFLOW.format(
                    idx=selection_idx,
                    amount=len(dom_items)
                )
            )
        target_list_item = dom_items[selection_idx]
        target_list_item.click()

        resident_num_span = page.locator(f'xpath={XPATH_BALANCE_RESIDENT_NUM_SPAN}')
        resident_num_span.wait_for(state='visible', timeout=TIMEOUT)
        resident_id = int(resident_num_span.inner_text().strip())

        data_div = page.locator(f'xpath={XPATH_BALANCE_DATA_DIV}')
        data_div.wait_for(state='visible', timeout=TIMEOUT)
        detailed_data_divs = data_div.locator('> div')
        date_div, remain_div = detailed_data_divs.element_handles()

        _, date_span = date_div.query_selector_all('> span')
        datetime_string = (date_span.inner_text() or '').strip()
        ordinal_date = datetime.datetime.strptime(
            datetime_string,
            '%Y-%m-%d %H:%M:%S'
        ).toordinal()

        balance_div, est_remain_div = remain_div.query_selector_all('> div')
        _, balance_span, _ = balance_div.query_selector_all('> span')
        balance = float(balance_span.inner_text())
        _, est_remain_span, _ = est_remain_div.query_selector_all('> span')
        est_remain_days = int(est_remain_span.inner_text())
        result: BalanceInfoWithResidentID = {
            'ordinal_date': ordinal_date,
            'resident_id': resident_id,
            'balance': balance,
            'estimate_remain_days': est_remain_days
        }
        return result

    @staticmethod
    def _get_balance_residents_list_items(page: Page) -> List[ElementHandle]:
        """
        click button to get list items of available residents in /osgweb/userAcc page
        """
        resident_selection_button = page.locator(f'xpath={XPATH_BALANCE_RESIDENTS_DROP_DOWN_BUTTON}')
        resident_selection_button.wait_for(state='visible', timeout=TIMEOUT)
        resident_selection_button.click()

        drop_down_unordered_list = page.locator(f'xpath={XPATH_BALANCE_RESIDENTS_DROP_DOWN_MENU}')
        drop_down_unordered_list.wait_for(state='visible', timeout=TIMEOUT)
        resident_list_items = drop_down_unordered_list.locator('li')
        dom_items = [item for item in resident_list_items.element_handles()]
        return dom_items
