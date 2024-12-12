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


try:
    from settings_local import *
except ImportError:
    pass
