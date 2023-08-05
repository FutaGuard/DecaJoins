from itertools import chain, cycle, repeat
from unittest import mock

import pytest

from bot.plugins.doh import HINT, cmd_help, doh, parse_args


pytestmark = [pytest.mark.asyncio]


def custom_time():
    return cycle(chain.from_iterable(zip(repeat(0), (1000, 1500, 2000))))


def with_hint(s):
    param = f'{HINT}\n{s}'
    return param


@pytest.mark.parametrize(
    'text, expected',
    (
        pytest.param(
            '/doh -q google',
            None,
            marks=pytest.mark.xfail(reason="tld not supported yet"),
        ),
        ('/doh -q google.com', None),
        ('/doh', with_hint('缺少 -q 參數')),
        ('/doh -q google.com -t error', with_hint('-t type 參數錯誤')),
        ('/doh -q google.com -s 1.1.1.1', with_hint('-s DoH 伺服器格式錯誤')),
        ('/doh -q google.com -b 1', with_hint('-b benchmark 次數設定錯誤')),
        ('/doh -q google.com -b 31', with_hint('-b benchmark 次數設定錯誤')),
        ('/doh -q google.com -b error', with_hint('-b benchmark 次數設定錯誤')),
        ('/doh -q google.com -R error', with_hint('-R raw 參數錯誤')),
    ),
)
async def test_cmd_help(text, expected):
    message = mock.AsyncMock()
    message.text = text
    await cmd_help(None, None, message)
    if expected is not None:
        message.reply_text.assert_awaited_with(expected)
    else:
        message.reply_text.assert_not_awaited()


@pytest.mark.parametrize(
    'text, answer, expected',
    (
        (
            '/doh -q google.com',
            'google.com. 275 IN A 172.217.163.46',
            '''\
🔍 查詢結果:
<code>{answer}</code>

⏳ 快樂錶: 1000.0s''',
        ),
        (
            '/doh -q google.com -b 3',
            'google.com. 875 IN A 172.217.163.46',
            '''\
🔍 查詢結果:
<code>{answer}</code>

🏁 測試結果:
1. - <code>1000.0s</code>
2. - <code>1500.0s</code>
3. - <code>2000.0s</code>

🤌 平均: <code>1500.0s</code>''',
        ),
    ),
)
async def test_doh(text, answer, expected):
    with mock.patch(
        'bot.utils.timing.time.time', side_effect=custom_time()
    ) as t, mock.patch(
        'bot.plugins.doh.doh_query',
        return_value=mock.AsyncMock(
            answer=[mock.MagicMock(**{'to_text.return_value': answer})]
        ),
    ) as query:
        client = mock.AsyncMock(**{'config.slave.enable': False})
        message = mock.AsyncMock(text=text)
        args = text.split(' ')[1:]
        parsed = parse_args(args)
        await doh(client, message)
        query.assert_awaited_with(parsed.server, parsed.query, parsed.type.upper())
        times = parsed.benchmark or 1
        assert query.call_count == times
        assert t.call_count == times * 2
        message.reply_text.assert_awaited_with(expected.format(answer=answer))


@pytest.mark.parametrize(
    'text, answer, expected',
    (
        (
            '/doh -q google.com',
            'google.com. 275 IN A 172.217.163.46',
            '''\
🔍 查詢結果（子節點）:

📍 <code>name (region)</code>
<code>ip（asn）</code>

<code>{answer}</code>

⏳ 快樂錶: 1000.0s''',
        ),
        (
            '/doh -q google.com -b 3',
            'google.com. 875 IN A 172.217.163.46',
            '''\
🔍 查詢結果（子節點）:

📍 <code>name (region)</code>
<code>ip（asn）</code>

<code>{answer}</code>

🏁 測試結果:
1. - <code>1000.0s</code>
2. - <code>1500.0s</code>
3. - <code>2000.0s</code>

🤌 平均: <code>1500.0s</code>''',
        ),
    ),
)
async def test_doh_standby(text, answer, expected):
    with mock.patch(
        'bot.utils.timing.time.time', side_effect=custom_time()
    ) as t, mock.patch(
        'bot.plugins.doh.doh_query',
        return_value=mock.AsyncMock(
            answer=[mock.MagicMock(**{'to_text.return_value': answer})]
        ),
    ) as query:
        client = mock.AsyncMock(
            **{
                'config.slave.enable': True,
                'config.slave.name': 'name',
                'slave.ip': 'ip',
                'slave.asn': 'asn',
                'slave.region': 'region',
            }
        )
        message = mock.AsyncMock(text=text)
        args = text.split(' ')[1:]
        parsed = parse_args(args)
        await doh(client, message)
        query.assert_awaited_with(parsed.server, parsed.query, parsed.type.upper())
        times = parsed.benchmark or 1
        assert query.call_count == times
        assert t.call_count == times * 2
        message.reply_text.assert_awaited_with(expected.format(answer=answer))


async def test_doh_error():
    with mock.patch(
        'bot.plugins.doh.doh_query', side_effect=ValueError('error')
    ) as query:
        client = mock.AsyncMock(
            **{
                'config.slave.enable': True,
                'config.slave.name': 'name',
                'slave.ip': 'ip',
                'slave.asn': 'asn',
                'slave.region': 'region',
            }
        )
        message = mock.AsyncMock(text='/doh -q google.com')
        await doh(client, message)
        query.assert_awaited_once()
        message.reply_text.assert_awaited_with('查詢錯誤，請先檢查 -s 參數是否正確')
