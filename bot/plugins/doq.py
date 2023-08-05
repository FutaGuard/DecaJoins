import argparse
import logging
from dataclasses import dataclass, field
from itertools import chain
from html import escape
from typing import List, Optional

import dns.asyncquery
import dns.message
import dns.query
import dns.rdatatype
from dataclasses_json import config, DataClassJsonMixin
from marshmallow import fields, validate, ValidationError
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types import Message

from bot import Bot
from bot.consts import SUPPORTED_DNS_TYPES
from bot.utils import ArgumentParser
from bot.utils.messages import has_standby, get_elapsed_info, get_standby_info
from bot.utils.timing import timing_handler
from bot.utils.validators import is_domain, is_quic

logger = logging.getLogger(__name__)
HINT = '使用方式: /doq -s <doq> -q <domain> -p <port> -t <type> -b <benchmark times>'


@dataclass
class Args(DataClassJsonMixin):
    server: str = field(metadata=config(
        field_name='s',
        mm_field=fields.Str(
            data_key='s',
            load_default='quic://unfiltered.adguard-dns.com',
            validate=is_quic,
            error_messages={
                'validator_failed': '-s DoQ 伺服器格式錯誤，應以 quic:// 作為開頭',
            },
        )
    ))
    query: str = field(metadata=config(
        field_name='q',
        mm_field=fields.Str(
            data_key='q',
            required=True,
            validate=is_domain,
            error_messages={
                'null': '缺少 -q 參數',
                'required': '缺少 -q 參數',
                'validator_failed': '-q query 網域格式錯誤',
            },
        )
    ))
    type: str = field(
        metadata=config(
            field_name='t',
            mm_field=fields.Str(
                data_key='t',
                load_default='A',
                validate=validate.OneOf(SUPPORTED_DNS_TYPES, error='-t type 參數錯誤'),
            )
        )
    )
    benchmark: Optional[int] = field(
        metadata=config(
            field_name='b',
            mm_field=fields.Int(
                data_key='b',
                load_default=None,
                validate=validate.Range(
                    min=2,
                    max=30,
                    error='-b benchmark 次數設定錯誤'
                ),
                error_messages={
                    'invalid': '-b benchmark 次數設定錯誤',
                },
            )
        )
    )
    raw: Optional[bool] = field(metadata=config(
        field_name='R',
        mm_field=fields.Boolean(
            data_key='R',
            load_default=False,
            error_messages={
                'invalid': '-R raw 參數錯誤',
            },
        )
    ))
    port: int = field(metadata=config(
        field_name='p',
        mm_field=fields.Int(
            data_key='p',
            load_default=853,
            validate=validate.Range(min=0, max=65536, error='-p port 參數錯誤'),
            error_messages={
                'invalid': '-p port 參數錯誤',
            },
        )
    ))

SCHEMA = Args.schema()


def parse_args(string: List[str]) -> Args:
    parser = ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('-s', type=str, help='some doq', required=False)
    parser.add_argument('-p', type=str, help='some ports', required=False)
    parser.add_argument('-q', type=str, help='some domain', required=False)
    parser.add_argument('-t', type=str, help='some type', required=False)
    parser.add_argument('-b', type=str, help='benchmark', required=False)
    parser.add_argument('-R', type=str, help='raw', required=False)
    return SCHEMA.load(vars(parser.parse_args(string)))


async def cmd_help(_, __, message: Message):
    cmd = message.text.split(' ')[1:]
    try:
        parse_args(cmd)
        return True
    except ValidationError as e:
        msg = '\n'.join(chain.from_iterable(e.messages_dict.values()))
        text = f'{HINT}\n{msg}'
        await message.reply_text(text)
        return False


async def doq_query(
    server: str, port: int, query: str, types: str
) -> dns.message.Message:
    return await dns.asyncquery.quic(
        q=dns.message.make_query(query, getattr(dns.rdatatype, types)),
        where=server,
        port=port,
    )


async def quick_resolve(qname: str) -> str:
    r = await dns.asyncquery.udp(
        q=dns.message.make_query(qname=qname, rdtype=dns.rdatatype.A), where='8.8.8.8'
    )
    if not len(r.answer):
        return ''
    else:
        return r.answer[0].to_text().split(' ')[-1]

async def command_handler(cmd: List[str]):
    args = parse_args(cmd)
    ip = await quick_resolve(args.server[7:])
    cnt = args.benchmark or 1
    results = [
        await timing_handler(doq_query, should_raise=True)(
            ip, args.port, args.query, args.type.upper()
        )
        for _ in range(cnt)
    ]
    first_result = results[0][0]
    # error already raised
    assert first_result
    answer = [first_result] if args.raw else first_result.answer
    result_block = ''.join(
        '<code>{result}</code>\n'.format(result=escape(r.to_text())) for r in answer
    )

    if len(results) == 1:
        elapsed_block = f'⏳ 快樂錶: {get_elapsed_info(results[0][1])}'
    else:
        steps = '\n'.join(
            f'{i}. - <code>{get_elapsed_info(elapsed)}</code>'
            for i, (_, elapsed) in enumerate(results, 1)
        )
        average = round(sum(elapsed for _, elapsed in results), 3) / cnt
        elapsed_block = '\n'.join(
            ['🏁 測試結果:', f'{steps}', f'\n🤌 平均: <code>{get_elapsed_info(average)}</code>']
        )
    return f'{result_block}\n{elapsed_block}'


@Client.on_message(
    filters.command('doq')
    & filters.create(cmd_help)  # pyright: ignore [reportGeneralTypeIssues]
)
async def doq(client: Bot, message: Message):
    cmd = message.text.split(' ')[1:]
    try:
        result = await command_handler(cmd)
    except Exception as e:
        await message.reply_text('查詢錯誤，請先檢查 -s 參數是否正確')
        logger.exception(e)
        return
    subtitle = ''
    standby_info = ''
    if has_standby(client):
        subtitle = '（子節點）'
        standby_info = f'\n{get_standby_info(client)}'
    title = f'🔍 查詢結果{subtitle}:'
    text = '\n'.join(filter(bool, (title, standby_info, result)))
    await message.reply_text(text)
