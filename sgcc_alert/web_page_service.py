"""
Service for SGCC web page manipulation
"""
import logging
import random
import time
from typing import List, Tuple

from playwright.sync_api import Page

from .notch_service import NotchService


logger = logging.getLogger(__name__)


TIMEOUT = 5 * 1000  # millisecond
WEB_URL_LOGIN = 'https://www.95598.cn/osgweb/login'


XPATH_LOGIN_BY_ACCOUNT = '//*[@id="login_box"]/div[1]/div[3]'
XPATH_ACCOUNT_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[1]/div/div/input'
XPATH_PASSWORD_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[2]/div/div/input'
XPATH_AGREE_TOS_CHECKBOX = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[3]/div/span[2]'
XPATH_LOGIN_BUTTON = '//*[@id="login_box"]/div[2]/div[1]/form/div[2]/div/button'
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


DRAG_SLIDE_SPEED_UP_RATIO = 0.8
DRAG_SLIDE_SPEED_UP_ACCELERATION = 10.0
DRAG_SLIDE_TIME_STEP = 0.1
SLIDE_X_OFFSET_FACTOR = 1.05


REFRESH_CAPTCHA_RETRY_LIMIT = 5


class LoginError(Exception):

    pass


class CaptchaValidationError(LoginError):

    pass


class LoginRateLimitError(LoginError):

    pass


class LoginAccountPasswordError(LoginError):

    pass


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
        page.wait_for_timeout(10)

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
            page.wait_for_timeout(TIMEOUT)
            x_ordinate, _ = self._recognize_notch_ordinate(page)
            retries += 1

        # raise without attempt to save daily login times limit
        if x_ordinate == 0:
            raise CaptchaValidationError(ERR_MSG_CAPTCHA_WRONG)

        # the factor on x_offset is from experience
        # which makes the slide block being in place
        self._slide_block(page, x_ordinate * SLIDE_X_OFFSET_FACTOR)
        page.wait_for_timeout(TIMEOUT)

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

    def _recognize_notch_ordinate(self, page: Page) -> Tuple[int, int]:
        bg_data_url, slide_data_url = self._identify_slide_captcha(page)
        notch_service = NotchService(bg_data_url, slide_data_url)
        x_ordinate, y_ordinate = notch_service.recognize_notch()
        return x_ordinate, y_ordinate
