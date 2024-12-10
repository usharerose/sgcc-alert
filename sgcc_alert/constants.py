"""
Constants
"""
from enum import Enum


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
SGCC_TIMEOUT_LOAD_PAGE = 3 * 1000


# ###########################################################
#  'State Grid Corporation of China' Web Page HTML selectors
# ###########################################################
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
    'xpath=/html/body/div/div/div/article/div/div/div[2]/div/div/div[1]/div[2]'
    '/div/div/div/div[2]/div[1]/div/div[1]/div/div[1]/div[2]/div/div/div'
)
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


# ###########################################################
#  'State Grid Corporation of China' Date Constants
# ###########################################################
class DateGranularity(Enum):

    DAILY = 'daily'
    MONTHLY = 'monthly'


DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


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
