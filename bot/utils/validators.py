from typing import Any, Callable, TypeVar

import validators

T = TypeVar('T')


def bool_wrapper(validator: Callable[[T], Any]):
    def inner(v: T):
        return bool(validator(v))

    return inner


def is_quic(v: str):
    return v.startswith('quic://')


def is_ip(s: str):
    return bool(validators.ipv4(s)) or bool(validators.ipv6(s))


# TODO: support tld
is_domain = bool_wrapper(validators.domain)
is_url = bool_wrapper(validators.url)
