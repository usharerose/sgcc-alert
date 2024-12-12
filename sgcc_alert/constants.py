"""
Constants
"""
from enum import Enum
import re


# ############################################
#  'State Grid Corporation of China' Web URLs
# ############################################
SGCC_WEB_URL_BALANCE = 'https://www.95598.cn/osgweb/userAcc'
SGCC_WEB_URL_DOOR_NUMBER_MANAGER = 'https://www.95598.cn/osgweb/doorNumberManeger'
SGCC_WEB_URL_LOGIN = 'https://www.95598.cn/osgweb/login'
SGCC_WEB_URL_MY_ACCOUNT = 'https://www.95598.cn/osgweb/my95598'
SGCC_WEB_URL_USAGE_HIST = 'https://www.95598.cn/osgweb/electricityCharge'


# ###################################################
#  'State Grid Corporation of China' HTTP parameters
# ###################################################
SGCC_TIMEOUT = 10 * 1000  # millisecond
SGCC_TIMEOUT_LOAD_CAPTCHA = 8 * 1000
SGCC_TIMEOUT_LOAD_PAGE = 3 * 1000


# ###########################################################
#  'State Grid Corporation of China' Web Page HTML selectors
# ###########################################################
SGCC_SELECTOR_LOGIN_CAPTCHA_BG_IMG = '#slideVerify > canvas:nth-child(1)'
SGCC_SELECTOR_LOGIN_CAPTCHA_BLOCK_IMG = '#slideVerify > canvas.slide-verify-block'
SGCC_SELECTOR_LOGIN_ERR_TIPS_CLASS = '.errmsg-tip'
SGCC_XPATH_BALANCE_DETAILED_DIV = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div'
    '/div[1]/div[2]/div/div/div/div[2]/div/div[2]/div[1]/div'
)
SGCC_XPATH_BALANCE_RESIDENT_ID_SPAN = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div/div[1]'
    '/div[2]/div/div/div/div[2]/div/div[1]/div/ul/div/li[1]/span[2]'
)
SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_BUTTON = (
    '//*[@id="app"]/div/div/article/div/div/div[2]/div/div/div[1]/div[2]'
    '/div/div/div/div[2]/div/div[1]/div/ul/li/div[2]/div[1]/span/span/i'
)
SGCC_XPATH_BALANCE_RESIDENTS_DROPDOWN_MENU = '/html/body/div[2]/div[1]/div[1]/ul'
SGCC_XPATH_DOORNUM_MANAGER_DETAILED_DIV = (
    '/html/body/div/div/div/article/div/div/div[2]/div/div/div[1]/div[2]'
    '/div/div/div/div[2]/div[1]/div/div[1]/div/div[1]/div[2]/div/div/div'
)
SGCC_XPATH_LOGIN_AGREE_TOS_CHECKBOX = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[3]/div/span[2]'
SGCC_XPATH_LOGIN_BUTTON = '//*[@id="login_box"]/div[2]/div[1]/form/div[2]/div/button'
SGCC_XPATH_LOGIN_BY_ACCOUNT_BUTTON = '//*[@id="login_box"]/div[1]/div[3]'
SGCC_XPATH_LOGIN_CAPTCHA_REFRESH_BUTTON = '//*[@id="slideVerify"]/div[1]'
SGCC_XPATH_LOGIN_CAPTCHA_SLIDE_BUTTON = '//*[@id="slideVerify"]/div[2]/div/div'
SGCC_XPATH_LOGIN_PASSWORD_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[2]/div/div/input'
SGCC_XPATH_LOGIN_USERNAME_INPUT = '//*[@id="login_box"]/div[2]/div[1]/form/div[1]/div[1]/div/div/input'
SGCC_XPATH_USAGE_HIST_DAILY_DETAILED_TBODY = (
    '//*[@id="pane-second"]/div[2]/div[2]/div[1]/div[3]/table/tbody'
)
SGCC_XPATH_USAGE_HIST_DAILY_RECENT_THIRTY_DAYS_CHECKBOX_SPAN = (
    '//*[@id="pane-second"]/div[1]/div/label[2]/span[1]'
)
SGCC_XPATH_USAGE_HIST_DAILY_TAB_DIV = '//*[@id="tab-second"]'
SGCC_XPATH_USAGE_HIST_MONTHLY_DETAILED_TBODY = (
    '//*[@id="pane-first"]/div[1]/div[2]/div[2]/div/div[3]/table/tbody'
)
SGCC_XPATH_USAGE_HIST_MONTHLY_TAB_DIV = '//*[@id="tab-first"]'
SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN = (
    '/html/body/div[3]/div[1]/div[1]/ul'
)
SGCC_XPATH_USAGE_HIST_MONTHLY_YEARS_DROPDOWN_BUTTON = (
    '//*[@id="pane-first"]/div[1]/div[1]/div[1]/div'
)
SGCC_XPATH_USAGE_HIST_RESIDENT_ID_SPAN = (
    '//*[@id="main"]/div/div[1]/div/ul/div/li[1]/span[2]'
)
SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN = (
    '/html/body/div[2]/div[1]/div[1]/ul'
)
SGCC_XPATH_USAGE_HIST_RESIDENTS_DROPDOWN_BUTTON = (
    '//*[@id="main"]/div/div[1]/div/ul/li/div[2]/div[1]/span/span/i'
)
SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN = (
    '/html/body/div[3]/div[1]/div[1]/ul'
)
SGCC_XPATH_USAGE_HIST_YEAR_DROPDOWN_BUTTON = (
    '//*[@id="pane-first"]/div[1]/div[1]/div[1]/div'
)


# ##################################################
#  'State Grid Corporation of China' Date Constants
# ##################################################
class DateGranularity(Enum):

    DAILY = 'daily'
    MONTHLY = 'monthly'


DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


# #################################################
#  'State Grid Corporation of China' Login Captcha
# #################################################
SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_RATIO = 0.8
SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_SPEED_UP_ACCELERATION = 10.0
SGCC_LOGIN_CAPTCHA_DRAG_SLIDE_TIME_STEP = 0.1
SGCC_LOGIN_CAPTCHA_SLIDE_X_OFFSET_FACTOR = 1.05
SGCC_LOGIN_CAPTCHA_REFRESH_RETRY_LIMIT = 5


# ###############
#  Error Message
# ###############
ERR_MSG_LOAD_RESIDENT_DETAILS_FAILED = (
    'Load resident info from /osgweb/doorNumberManeger failed'
)
ERR_MSG_TML_OVERFLOW = ((
    'Requested {serial} {entity_name} is overflowed '
    'than available capacity: {amount}'
))
ERR_MSG_WRONG_ACCOUNT_PWD = '账号或密码错误，如连续错误5次，账号将被锁定20分钟，20分钟后自动解锁。'
ERR_MSG_REACH_LOGIN_LIMIT = '网络连接超时（RK001）,请重试！'
ERR_MSG_CAPTCHA_WRONG = '验证错误！'


SGCC_SCRIPT_TPL_IMG_ENCODE = '''
    () => {{
      const bgImgCanvas = document.querySelector('{selector}');
      if (bgImgCanvas) {{
        return bgImgCanvas.toDataURL('image/png');
      }}
      return null;
    }}
'''


# ##########################################
#  Captcha notch computer vision parameters
# ##########################################
CANNY_LOWER_THRESHOLD = 50
CANNY_UPPER_THRESHOLD = 100
CV_BINARY_THRESH = 45.0
CV_BINARY_MAXVAL = 255.0
CV_KERNAL_SIZE = 4


# ##########
#  Database
# ##########
DATABASE_INIT_RETRY_LIMIT = 3


# #################
#  Settings object
# #################
ENVIRONMENT_VARIABLE = 'SGCC_SETTINGS_MODULE'
DEFAULT_SETTINGS_MODULE = 'settings'
SETTING_KEY_MAX_LENGTH = 100
SETTING_KEY_MATCH = re.compile(r'^[a-zA-Z0-9_-]+$').match
