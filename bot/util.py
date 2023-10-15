'''
Utility functions.
'''

import logging
import time

logger = logging.getLogger(__name__)


def retry(times=10, exceptions=Exception):
    '''Retries the function it decorates if it raises an exception.'''

    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 1
            while attempt <= times:

                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error(
                        'Run %d: Exception executing %s', attempt, func)
                    logger.error(e, exc_info=True)

                    attempt += 1
                    time.sleep(30 * attempt)

            return func(*args, **kwargs)
        return newfn
    return decorator
