from itertools import chain, cycle, repeat
from unittest import mock

import pytest

from bot.plugins.doq import HINT, cmd_help, doq, parse_args

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures('mock_tld')]


def custom_time():
    return cycle(chain.from_iterable(zip(repeat(0), (1000, 1500, 2000))))


def with_hint(s):
    param = f'{HINT}\n{s}'
    return param


@pytest.mark.parametrize(
    'text, expected',
    (
        ('/doq -q gg.', None),
        ('/doq -q google', None),
        ('/doq -q google.com', None),
        ('/doq', with_hint('缺少 -q 參數')),
        ('/doq -q invalid', with_hint('-q query 網域格式錯誤')),
        ('/doq -q google -t error', with_hint('-t type 參數錯誤')),
        (
            '/doq -q google -s https://google.com',
            with_hint('-s DoQ 伺服器格式錯誤，應以 quic:// 作為開頭'),
        ),
        ('/doq -q google -b 1', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google -b 31', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google -b error', with_hint('-b benchmark 次數設定錯誤')),
        ('/doq -q google -p error', with_hint('-p port 參數錯誤')),
        ('/doq -q google -R error', with_hint('-R raw 參數錯誤')),
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
            '/doq -q google.com',
            'google.com. 275 IN A 172.217.163.46',
            '''\
🔍 查詢結果:
<code>{answer}</code>

⏳ 快樂錶: 1000.0s''',
        ),
        (
            '/doq -q google.com -b 3',
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
async def test_doq(text: str, answer, expected):
    with mock.patch(
        'bot.utils.timing.time.time', side_effect=custom_time()
    ) as t, mock.patch(
        'bot.plugins.doq.quick_resolve', return_value='94.140.14.140'
    ) as resolve, mock.patch(
        'bot.plugins.doq.doq_query',
        return_value=mock.AsyncMock(
            answer=[mock.MagicMock(**{'to_text.return_value': answer})]
        ),
    ) as query:
        client = mock.AsyncMock(**{'config.slave.enable': False})
        message = mock.AsyncMock(text=text)
        args = text.split(' ')[1:]
        parsed = parse_args(args)
        await doq(client, message)
        query.assert_awaited_with(
            resolve.return_value, parsed.port, parsed.query, parsed.type.upper()
        )
        times = parsed.benchmark or 1
        assert query.call_count == times
        assert t.call_count == times * 2
        message.reply_text.assert_awaited_with(expected.format(answer=answer))


@pytest.mark.parametrize(
    'text, answer, expected',
    (
        (
            '/doq -q google.com',
            'google.com. 275 IN A 172.217.163.46',
            '''\
🔍 查詢結果（子節點）:

📍 <code>name (region)</code>
<code>ip（asn）</code>

<code>{answer}</code>

⏳ 快樂錶: 1000.0s''',
        ),
        (
            '/doq -q google.com -b 3',
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
async def test_doq_standby(text, answer, expected):
    with mock.patch(
        'bot.utils.timing.time.time', side_effect=custom_time()
    ) as t, mock.patch(
        'bot.plugins.doq.quick_resolve', return_value='94.140.14.140'
    ) as resolve, mock.patch(
        'bot.plugins.doq.doq_query',
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
        await doq(client, message)
        query.assert_awaited_with(
            resolve.return_value, parsed.port, parsed.query, parsed.type.upper()
        )
        times = parsed.benchmark or 1
        assert query.call_count == times
        assert t.call_count == times * 2
        message.reply_text.assert_awaited_with(expected.format(answer=answer))


async def test_doq_error():
    with mock.patch(
        'bot.plugins.doq.doq_query', side_effect=ValueError('error')
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
        message = mock.AsyncMock(text='/doq -q google.com')
        await doq(client, message)
        query.assert_awaited_once()
        message.reply_text.assert_awaited_with('查詢錯誤，請先檢查 -s 參數是否正確')
