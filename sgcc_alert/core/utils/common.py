"""
Common utilities
"""
from functools import wraps
import logging
import time
from typing import Any, Callable, Tuple


logger = logging.getLogger(__name__)


def retry(
    retry_limit: int = 3,
    delay: float = 1.0,
    exceptions: Tuple = (Exception,),
    backoff_factor: float = 2.0
) -> Callable:
    """
    A decorator to retry a function if it raises specified exceptions
    :params retry_limit: maximum number of retries before giving up
    :type retry_limit: int
    :params delay: delay between retries in seconds
    :type delay: float
    :params exceptions: exception classes to catch and retry on
    :type exceptions: tuple
    :params backoff_factor: multiplier applied to the delay after each retry
    :type backoff_factor: float
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            delay_value = delay
            while retries < retry_limit:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= retry_limit:
                        logger.exception(e)
                        raise
                    logger.warning(
                        f'Retrying {func.__name__} {retries} / {retry_limit} '
                        f'when meet exception: {e}'
                    )
                    time.sleep(delay_value)
                    delay_value *= backoff_factor

        return wrapper

    return decorator


def get_ordinal_suffix(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return 'th'
    units_digit = value % 10
    if units_digit == 1:
        return 'st'
    if units_digit == 2:
        return 'nd'
    if units_digit == 3:
        return 'rd'
    return 'th'
