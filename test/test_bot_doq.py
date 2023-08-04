import pytest
from unittest import mock

from bot.plugins.doq import cmd_help, HINT

pytestmark = [pytest.mark.asyncio]


def with_hint(s):
    param = f'{HINT}\n{s}'
    return param


@pytest.mark.parametrize(
    'text, expected',
    (
        pytest.param(
            '/doq -q google',
            None,
            marks=pytest.mark.xfail(reason="tld not supported yet"),
        ),
        ('/doq -q google.com', None),
        ('/doq', with_hint('缺少 -q 參數')),
        ('/doq -q google.com -t error', with_hint('-t type 參數錯誤')),
        (
            '/doq -q google.com -s https://google.com',
            with_hint('-s DoQ 伺服器格式錯誤，應以 quic:// 作為開頭'),
        ),
        ('/doq -q google.com -b 1', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google.com -b 31', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google.com -b error', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google.com -p error', with_hint('-p port 參數錯誤')),
        ('/doq -q google.com -R error', with_hint('-R raw 參數錯誤')),
    ),
)
async def test_cmd_help(text, expected):
    message = mock.AsyncMock()
    message.text = text
    await cmd_help(None, None, message)
    if expected is not None:
        message.reply_text.assert_called_with(expected)
    else:
        message.reply_text.assert_not_called()
