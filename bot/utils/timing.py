import logging
import time


logger = logging.getLogger(__name__)


def timing_handler(func, *, should_raise=False):
    async def async_wrapper(*args, **kw):
        start = time.time()
        try:
            r = await func(*args, **kw)
        except Exception as e:
            logger.exception(e)
            if should_raise:
                raise
            r = None
        # to ms
        elapsed = (time.time() - start) * 1e3
        return (r, elapsed)

    return async_wrapper
