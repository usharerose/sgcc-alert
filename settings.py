"""
settings
"""
DEBUG = False


DATABASES = {
    'default': {
        'ENGINE': 'sqlite',
        'NAME': 'sgcc.sqlite'
    }
}


SGCC_ACCOUNT_USERNAME = 'admin'
SGCC_ACCOUNT_PASSWORD = 'admin'


POLL_INTERVAL = 5
# the time when executing daily task
# 24-hour system
# 'HH:SS' format
DAILY_CRON_TIME = '06:00'


try:
    from settings_local import *
except ImportError:
    pass
