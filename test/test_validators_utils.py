from unittest import mock

import httpx
import pytest

from bot.utils.validators import get_tld, is_domain

pytestmark = [pytest.mark.asyncio]


@mock.patch('bot.utils.validators.http')
@mock.patch('bot.utils.validators._TLD', autospec=True)
async def test_get_tld(t, h):
    h.get.return_value.text = "GG\nGOOGLE"
    r = get_tld()
    assert r == set(["GG", "GOOGLE"])
    h.get.assert_called_once()

    h.get.return_value.text = "GG\nGOOGLE\nHK"
    # only fetch once
    r = get_tld()
    assert r == set(["GG", "GOOGLE"])
    h.get.assert_called_once()

    # update with force
    r = get_tld(force=True)
    assert r == set(["GG", "GOOGLE", "HK"])
    assert h.get.call_count == 2


@mock.patch('bot.utils.validators.http')
@mock.patch('bot.utils.validators._TLD')
async def test_fetch_tld_error(t, h):
    for i, e in enumerate(
        (
            httpx.HTTPStatusError(
                "Invalid status code",
                request=mock.MagicMock(),
                response=mock.MagicMock(),
            ),
            httpx.RequestError("Request error", request=mock.MagicMock()),
            httpx.HTTPError("HTTP error"),
        ),
        1,
    ):
        h.get.return_value.raise_for_status.side_effect = e
        r = get_tld(force=True)
        assert r == t
        assert h.get.call_count == i


@pytest.mark.parametrize(
    'text, expected',
    (
        ('gg.', True),
        ('gg', True),
        ('apple', True),
        ('google', False),
    ),
)
async def test_is_domain_support_tld(text, expected):
    with mock.patch('bot.utils.validators.http') as h:
        h.get.return_value.text = "APPLE\nGG"
        get_tld(force=True)
        assert is_domain(text) == expected
