'''
Utility functions.
'''

import logging
import time

from datetime import datetime

logger = logging.getLogger(__name__)


def retry(times=20, exceptions=Exception):
    '''Retries the function it decorates if it raises an exception.'''

    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 1
            while attempt <= times:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error('Run %d: Exception executing %s', attempt, func)
                    logger.error(e, exc_info=True)

                    attempt += 1
                    time.sleep(60 * attempt)

            return func(*args, **kwargs)

        return newfn

    return decorator


def enough_delay(delay_seconds, start, end=None):
    '''Checks if enough time has passed since start.

    Arguments:
        delay_seconds:
        start:
        end:

    Returns:
        True or False
    '''

    if end is None:
        end = datetime.now()
    return (end - start).total_seconds() > delay_seconds
