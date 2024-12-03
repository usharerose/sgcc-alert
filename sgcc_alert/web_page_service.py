"""
Service for SGCC web page manipulation
"""
from typing import Tuple

from playwright.sync_api import Browser, Page


TIMEOUT = 5 * 1000  # milisecond
WEB_URL_LOGIN = 'https://www.95598.cn/osgweb/login'


XPATH_LOGIN_BY_ACCOUNT = '//*[@id="login_box"]/div[1]/div[3]'
XPATH_ACCOUNT_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[1]/div/div/input'
XPATH_PASSWORD_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[2]/div/div/input'
XPATH_AGREE_TOS_CHECKBOX = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[3]/div/span[2]'
XPATH_LOGIN_BUTTON = '//*[@id="login_box"]/div[2]/div[1]/form/div[2]/div/button'
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


class WebPageService:

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def login(self, browser: Browser) -> None:
        page = browser.new_page()
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

        self._verify_slide_captcha(page)

    def _verify_slide_captcha(self, page: Page) -> None:
        pass

    def _identify_slide_captcha(self, page: Page) -> Tuple[str, str]:
        """
        get data URL of canvas for slide captcha's
        background image and block image
        """
        bg_img_script = SCRIPT_TPL_IMG_ENCODE.format(selector=SELECTOR_CAPTCHA_BG_IMG)
        bg_img_data_url = page.evaluate(bg_img_script)

        block_img_script = SCRIPT_TPL_IMG_ENCODE.format(selector=SELECTOR_CAPTCHA_BLOCK_IMG)
        block_img_data_url = page.evaluate(block_img_script)
        return bg_img_data_url, block_img_data_url
