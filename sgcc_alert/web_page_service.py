"""
Service for SGCC web page manipulation
"""
import random
from typing import Tuple

from playwright.sync_api import Browser, Page

from sgcc_alert.notch_service import NotchService


TIMEOUT = 10 * 1000  # millisecond
WEB_URL_LOGIN = 'https://www.95598.cn/osgweb/login'


XPATH_LOGIN_BY_ACCOUNT = '//*[@id="login_box"]/div[1]/div[3]'
XPATH_ACCOUNT_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[1]/div/div/input'
XPATH_PASSWORD_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[2]/div/div/input'
XPATH_AGREE_TOS_CHECKBOX = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[3]/div/span[2]'
XPATH_LOGIN_BUTTON = '//*[@id="login_box"]/div[2]/div[1]/form/div[2]/div/button'
XPATH_CAPTCHA_SLIDE_BUTTON = '//*[@id="slideVerify"]/div[2]/div/div'
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
DRAG_SLIDE_SPEED_UP_ACCELERATION = 10
DRAG_SLIDE_TIME_STEP = 0.1


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

        self._verify_slide_captcha(page)

    def _verify_slide_captcha(self, page: Page) -> None:
        bg_data_url, slide_data_url = self._identify_slide_captcha(page)
        notch_service = NotchService(bg_data_url, slide_data_url)
        x_offset, _ = notch_service.recognize_notch()

        self._slide_block(page, x_offset)
        page.wait_for_timeout(TIMEOUT)

        err_tip_div = page.locator(f'.{CLASS_LOGIN_ERR_TIPS}')
        if err_tip_div.is_visible():
            err_msg = err_tip_div.locator('span').text_content()
            if err_msg == ERR_MSG_REACH_LOGIN_LIMIT:
                raise LoginRateLimitError(f'Login rate limit error: {ERR_MSG_REACH_LOGIN_LIMIT}')
            if err_msg == ERR_MSG_CAPTCHA_WRONG:
                raise CaptchaValidationError(ERR_MSG_CAPTCHA_WRONG)
            if err_msg == ERR_MSG_WRONG_ACCOUNT:
                raise LoginAccountPasswordError(ERR_MSG_WRONG_ACCOUNT_PWD)
            raise LoginError(f'Login failed: {LoginError}')
        if page.url == WEB_URL_LOGIN:
            raise LoginError(f'Login failed with unknown error')

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
        slide_button = page.locator(f'xpath={XPATH_CAPTCHA_SLIDE_BUTTON}')
        slide_button_box = slide_button.bounding_box()
        box_x = slide_button_box['x'] + slide_button_box['width'] / 2
        box_y = slide_button_box['y'] + slide_button_box['height'] / 2

        page.mouse.move(box_x, box_y)
        page.mouse.down()
        for sub_x_offset in self.simulate_horizontal_move_tracks(x_offset):
            sub_dest_x = box_x + sub_x_offset

            # simulate the shake when slide
            sub_y_offset = random.uniform(-2, 2)
            sub_dest_y = box_y + sub_y_offset

            page.mouse.move(sub_dest_x, sub_dest_y)
        page.mouse.up()

    @staticmethod
    def simulate_horizontal_move_tracks(x_offset: float):
        """
        build tracing point with speed up and speed down
        to imitate human-machine interaction
        """
        tracks = []
        cur_offset = 0
        # move getting slow down near the end of the distance
        mid = x_offset * DRAG_SLIDE_SPEED_UP_RATIO
        velocity = 0
        while cur_offset < x_offset:
            acceleration = DRAG_SLIDE_SPEED_UP_ACCELERATION  # speed up
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
