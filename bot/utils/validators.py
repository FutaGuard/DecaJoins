from typing import Any, Callable, TypeVar

import validators
from coloredlogs import logging

from bot.utils.http import HTTPError, http

logger = logging.getLogger(__name__)

T = TypeVar('T')


def bool_wrapper(validator: Callable[[T], Any]):
    def inner(v: T):
        return bool(validator(v))

    return inner


def is_quic(v: str):
    return v.startswith('quic://')


def is_ip(s: str):
    return bool(validators.ipv4(s)) or bool(validators.ipv6(s))


_TLD = set()


# lazy initialized
def get_tld(*, force: bool = False):
    global _TLD
    if not _TLD or force:
        try:
            response = http.get('https://data.iana.org/TLD/tlds-alpha-by-domain.txt')
            response.raise_for_status()
            data = response.text
        except HTTPError as e:
            logger.exception(e)
        else:
            _TLD = set(data.split('\n'))
    return _TLD


def is_domain(s: str):
    return (
        bool(validators.domain(s, rfc_1034=True, rfc_2782=True))
        or s.rstrip('.').upper() in get_tld()
    )


is_url = bool_wrapper(validators.url)
