"""
Utilities on login
"""
import logging
import random
import time
from typing import List, Tuple

from playwright.sync_api import Page
from playwright._impl._errors import TimeoutError  # NOQA

from ..constants import (
    ERR_MSG_CAPTCHA_WRONG,
    ERR_MSG_REACH_LOGIN_LIMIT,
    ERR_MSG_WRONG_ACCOUNT_PWD,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_ACCELERATION,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP,
    SGCC_LOGIN_CAPTCHA_SLIDE_X_OFFSET_FACTOR,
    SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT,
    SGCC_SCRIPT_TPL_IMG_ENCODE,
    SGCC_SELECTOR_LOGIN_CAPTCHA_BG_IMG,
    SGCC_SELECTOR_LOGIN_CAPTCHA_BLOCK_IMG,
    SGCC_TIMEOUT,
    SGCC_TIMEOUT_LOAD_CAPTCHA,
    SGCC_TIMEOUT_LOAD_PAGE,
    SGCC_WEB_URL_LOGIN,
    SGCC_SELECTOR_LOGIN_ERR_TIPS_CLASS,
    SGCC_XPATH_LOGIN_AGREE_TOS_CHECKBOX,
    SGCC_XPATH_LOGIN_BUTTON,
    SGCC_XPATH_LOGIN_BY_ACCOUNT_BUTTON,
    SGCC_XPATH_LOGIN_CAPTCHA_REFRESH_BUTTON,
    SGCC_XPATH_LOGIN_CAPTCHA_SLIDE_BUTTON,
    SGCC_XPATH_LOGIN_PASSWORD_INPUT,
    SGCC_XPATH_LOGIN_USERNAME_INPUT
)
from ..exceptions import (
    CaptchaValidationError,
    LoginAccountPasswordError,
    LoginError,
    LoginRateLimitError
)
from ..notch_service import NotchService


logger = logging.getLogger(__name__)


__all__ = ['login']


def login(page: Page, username: str, password: str) -> None:
    page.goto(url=SGCC_WEB_URL_LOGIN, timeout=SGCC_TIMEOUT)

    login_by_account_button_locator = page.locator(
        f'xpath={SGCC_XPATH_LOGIN_BY_ACCOUNT_BUTTON}'
    )
    login_by_account_button_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    login_by_account_button_locator.click()

    username_form_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_USERNAME_INPUT}')
    username_form_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    username_form_locator.fill(username)
    pwd_form_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_PASSWORD_INPUT}')
    pwd_form_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    pwd_form_locator.fill(password)

    tos_checkbox_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_AGREE_TOS_CHECKBOX}')
    tos_checkbox_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    tos_checkbox_locator.click()

    login_button_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_BUTTON}')
    login_button_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    login_button_locator.click()
    # captcha image loading costs much more time
    page.wait_for_timeout(SGCC_TIMEOUT_LOAD_CAPTCHA)

    _verify_slide_captcha_with_retry(page)


def _verify_slide_captcha_with_retry(page: Page) -> None:
    retries = 0
    while True:
        try:
            _verify_slide_captcha(page)
        except CaptchaValidationError:
            if retries < SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT:
                time.sleep(1)
                retries += 1
            else:
                break
        except (LoginRateLimitError, LoginAccountPasswordError, LoginError):
            raise
        else:
            break


def _verify_slide_captcha(page: Page) -> None:
    x_ordinate, _ = _identify_notch_ordinate(page)

    # when x_ordinate is equal to 0, it means no effective identification
    retries = 0
    while x_ordinate == 0 and retries < SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT:
        _refresh_captcha(page)
        x_ordinate, _ = _identify_notch_ordinate(page)
        retries += 1

    # raise without attempt to save daily login times limit
    if x_ordinate == 0:
        raise CaptchaValidationError()

    # the factor on x_offset is from experience
    # which makes the slide block being in place
    _slide_block(page, x_ordinate * SGCC_LOGIN_CAPTCHA_SLIDE_X_OFFSET_FACTOR)

    err_tip_div = page.locator(SGCC_SELECTOR_LOGIN_ERR_TIPS_CLASS)
    if err_tip_div.is_visible():
        err_msg = err_tip_div.locator('span').text_content()
        if err_msg == ERR_MSG_REACH_LOGIN_LIMIT:
            raise LoginRateLimitError(f'Login rate limit error: {ERR_MSG_REACH_LOGIN_LIMIT}')
        if err_msg == ERR_MSG_CAPTCHA_WRONG:
            raise CaptchaValidationError()
        if err_msg == ERR_MSG_WRONG_ACCOUNT_PWD:
            raise LoginAccountPasswordError()
        raise LoginError(f'Login failed: {err_msg}')
    if page.url == SGCC_WEB_URL_LOGIN:
        raise LoginError('Login failed with unknown error')


def _refresh_captcha(page: Page) -> None:
    refresh_button_locator = page.locator(
        f'xpath={SGCC_XPATH_LOGIN_CAPTCHA_REFRESH_BUTTON}'
    )
    refresh_button_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')
    refresh_button_locator.click()
    page.wait_for_timeout(SGCC_TIMEOUT_LOAD_CAPTCHA)


def _identify_notch_ordinate(page: Page) -> Tuple[int, int]:
    bg_data_url, slide_data_url = _get_slide_captcha_raw_images(page)
    notch_service = NotchService(bg_data_url, slide_data_url)
    x_ordinate, y_ordinate = notch_service.locate_notch()
    return x_ordinate, y_ordinate


def _get_slide_captcha_raw_images(page: Page) -> Tuple[str, str]:
    """
    get data URL of canvas for slide captcha's
    background image and block image
    """
    bg_img_script = SGCC_SCRIPT_TPL_IMG_ENCODE.format(
        selector=SGCC_SELECTOR_LOGIN_CAPTCHA_BG_IMG
    )
    bg_img_data_url = page.evaluate(bg_img_script)

    slide_img_script = SGCC_SCRIPT_TPL_IMG_ENCODE.format(
        selector=SGCC_SELECTOR_LOGIN_CAPTCHA_BLOCK_IMG
    )
    slide_img_data_url = page.evaluate(slide_img_script)
    return bg_img_data_url, slide_img_data_url


def _slide_block(page: Page, x_offset: float) -> None:
    """
    assume the page is with captcha,
    verify by slide action with the distance according to given offset
    """
    slide_button_locator = page.locator(
        f'xpath={SGCC_XPATH_LOGIN_CAPTCHA_SLIDE_BUTTON}'
    )
    slide_button_locator.wait_for(timeout=SGCC_TIMEOUT, state='visible')

    slide_button_box = slide_button_locator.bounding_box()
    assert slide_button_box is not None
    slide_button_x_ordinate = slide_button_box['x'] + slide_button_box['width'] / 2
    slide_button_y_ordinate = slide_button_box['y'] + slide_button_box['height'] / 2

    page.mouse.move(slide_button_x_ordinate, slide_button_y_ordinate)
    page.mouse.down()
    for sub_x_offset in simulate_horizontal_move_tracks(x_offset):
        sub_dest_x = slide_button_x_ordinate + sub_x_offset

        # simulate the shake when slide
        sub_y_offset = random.uniform(-2, 2)
        sub_dest_y = slide_button_y_ordinate + sub_y_offset

        page.mouse.move(sub_dest_x, sub_dest_y)

    page.mouse.up()
    page.wait_for_timeout(SGCC_TIMEOUT_LOAD_PAGE)


def simulate_horizontal_move_tracks(x_offset: float) -> List[float]:
    """
    build tracing point with speed up and speed down
    to imitate human-machine interaction
    """
    tracks = []
    cur_offset = 0.0
    # move getting slow down near the end of the distance
    mid = x_offset * SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO
    velocity = 0.0
    while cur_offset < x_offset:
        acceleration: float = SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_ACCELERATION  # speed up
        if cur_offset >= mid:
            acceleration = (
                -1 * SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_ACCELERATION *
                SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO /
                (1 - SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO)
            )  # speed down at the second half
        span = (
            velocity * SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP +
            0.5 * acceleration * SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP ** 2
        )
        velocity = velocity + acceleration * SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP
        cur_offset += span
        tracks.append(round(cur_offset, 4))
    return tracks
