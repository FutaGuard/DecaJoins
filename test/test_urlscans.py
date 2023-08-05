from unittest import mock

import pytest

from bot.plugins.scanner import urlscan

pytestmark = [pytest.mark.asyncio]


@pytest.mark.parametrize(
    'text, expected',
    (
        ('/urlscan', '缺少參數'),
        ('/urlscan error', 'URL 格式錯誤'),
    ),
)
async def test_urlscan_error(text, expected):
    client = mock.MagicMock()
    message = mock.AsyncMock(text=text, command=text.split(' '))
    await urlscan(client, message)
    message.reply_text.assert_awaited_with(expected)
