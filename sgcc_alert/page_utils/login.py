"""
Utilities on login
"""
import logging
import random
from typing import List, Tuple

from playwright.sync_api import Page
from playwright._impl._errors import TimeoutError

from .common import load_locator
from ..common import retry
from ..constants import (
    ERR_MSG_ACCOUNT_NAME_INVALID,
    ERR_MSG_CAPTCHA_WRONG,
    ERR_MSG_REACH_LOGIN_LIMIT,
    ERR_MSG_WRONG_ACCOUNT_PWD,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_ACCELERATION,
    SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP,
    SGCC_LOGIN_CAPTCHA_SLIDE_X_OFFSET_FACTOR,
    SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT,
    SGCC_SCRIPT_TPL_IMG_ENCODE,
    SGCC_SCRIPT_TML_WAIT_CAPTCHA_CANVAS,
    SGCC_SELECTOR_LOGIN_CAPTCHA_BG_IMG,
    SGCC_SELECTOR_LOGIN_CAPTCHA_BLOCK_IMG,
    SGCC_TIMEOUT,
    SGCC_TIMEOUT_LOAD_CAPTCHA,
    SGCC_TIMEOUT_LOAD_PAGE,
    SGCC_PAGE_VISITING_INTERVAL,
    SGCC_WEB_URL_LOGIN,
    SGCC_SELECTOR_LOGIN_ERR_TIPS_CLASS,
    SGCC_XPATH_LOGIN_AGREE_TOS_CHECKBOX,
    SGCC_XPATH_LOGIN_BUTTON,
    SGCC_XPATH_LOGIN_BY_ACCOUNT_BUTTON,
    SGCC_XPATH_LOGIN_CAPTCHA_DIV,
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


@retry(
    retry_limit=SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT,
    exceptions=(CaptchaValidationError, TimeoutError)
)
def login(page: Page, username: str, password: str) -> None:
    """
    1. visit login page
    2. switch to username-password mode
    3. fill username and password, clicking agree term of service
    4. click login button, and break if
       * no captcha visible, and there is error tips reminding that username invalid
    """
    logger.info('start to login')
    page.goto(url=SGCC_WEB_URL_LOGIN, timeout=SGCC_TIMEOUT)

    _fill_login_form(page, username, password)
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    _popup_captcha_with_clicking_login(page, username)
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    _verify_slide_captcha(page)
    logger.info('login succeed')


def _fill_login_form(page: Page, username: str, password: str) -> None:
    login_by_account_button_locator = page.locator(
        f'xpath={SGCC_XPATH_LOGIN_BY_ACCOUNT_BUTTON}'
    )
    load_locator(login_by_account_button_locator)
    login_by_account_button_locator.click()
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    username_form_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_USERNAME_INPUT}')
    load_locator(username_form_locator)
    username_form_locator.fill(username)
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)
    pwd_form_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_PASSWORD_INPUT}')
    load_locator(pwd_form_locator)
    pwd_form_locator.fill(password)
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    tos_checkbox_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_AGREE_TOS_CHECKBOX}')
    load_locator(tos_checkbox_locator)
    tos_checkbox_locator.click()


def _popup_captcha_with_clicking_login(page: Page, username: str) -> None:
    login_button_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_BUTTON}')
    load_locator(login_button_locator)
    login_button_locator.click()
    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    _load_captcha(page, username)


def _load_captcha(page: Page, username: str) -> None:
    """
    check the captcha division and canvas visibility
    if username was invalid, there could be no captcha division
    """
    try:
        captcha_div_locator = page.locator(f'xpath={SGCC_XPATH_LOGIN_CAPTCHA_DIV}')
        captcha_div_locator.wait_for(timeout=SGCC_TIMEOUT_LOAD_PAGE)
    except TimeoutError:
        err_tip_div = page.locator(SGCC_SELECTOR_LOGIN_ERR_TIPS_CLASS)
        if err_tip_div.is_visible():
            err_msg = err_tip_div.locator('span').text_content()
            if err_msg == ERR_MSG_ACCOUNT_NAME_INVALID:
                raise LoginError(f'{ERR_MSG_ACCOUNT_NAME_INVALID}: {username}')
        raise

    page.wait_for_function(
        SGCC_SCRIPT_TML_WAIT_CAPTCHA_CANVAS.format(
            selector=SGCC_SELECTOR_LOGIN_CAPTCHA_BG_IMG
        ),
        timeout=SGCC_TIMEOUT_LOAD_CAPTCHA
    )


@retry(
    retry_limit=SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT,
    exceptions=(CaptchaValidationError,)
)
def _verify_slide_captcha(page: Page, username: str) -> None:
    x_ordinate, _ = _identify_notch_ordinate(page)

    # when x_ordinate is equal to 0, it means no effective identification
    retries = 0
    while x_ordinate == 0 and retries < SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT:
        logger.warning(
            f'Retrying identify captcha notch {retries} / {SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT}'
        )
        # choose re-click login button instead of clicking captcha refresh button
        # since the DOM of captcha canvas are always there
        # even though the new round image hasn't loaded,
        # which makes the judgement of successful loading difficult by wait for DOM visible
        page.keyboard.press('Escape')
        page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)
        _popup_captcha_with_clicking_login(page, username)

        x_ordinate, _ = _identify_notch_ordinate(page)
        retries += 1
        page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    # raise without attempt to save daily login times limit
    if x_ordinate == 0:
        raise CaptchaValidationError()

    page.wait_for_timeout(timeout=SGCC_PAGE_VISITING_INTERVAL)

    # the factor on x_offset is from experience
    # which makes the slide block being in place
    _slide_block(page, x_ordinate * SGCC_LOGIN_CAPTCHA_SLIDE_X_OFFSET_FACTOR)

    page.wait_for_timeout(timeout=SGCC_TIMEOUT_LOAD_PAGE)

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
    load_locator(slide_button_locator)

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
