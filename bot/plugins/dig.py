import argparse
import time
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
from bot.utils.validators import is_ip, is_domain


HINT = '使用方式: /dig -s <udp ip> -q <domain> -t <type>'


@dataclass
class Args(DataClassJsonMixin):
    server: str = field(metadata=config(
        field_name='s',
        mm_field=fields.Str(
            data_key='s',
            load_default='8.8.8.8',
            validate=is_ip,
            error_messages={
                'validator_failed': '-s UDP IP 伺服器格式錯誤',
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

SCHEMA = Args.schema()


def parse_args(string: List[str]) -> Args:
    parser = ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('-s', type=str, help='some server', required=False)
    parser.add_argument('-q', type=str, help='some domain', required=False)
    parser.add_argument('-t', type=str, help='some type', required=False)
    parser.add_argument('-b', type=str, help='benchmark', required=False)
    parser.add_argument('-R', type=str, help='raw', required=False)
    return SCHEMA.load(vars(parser.parse_args(string)))


async def cmd_help(_, __, message: Message):
    # /doh -s https://doh.futa.gg/dns-query -q google.com -t A
    # message.
    cmd = message.text.split(' ')[1:]
    try:
        parse_args(cmd)
        return True
    except ValidationError as e:
        msg = '\n'.join(chain.from_iterable(e.messages_dict.values()))
        text = f'{HINT}\n{msg}'
        await message.reply_text(text)
        return False


async def dig_query(server: str, query: str, types: str) -> dns.message.Message:
    r = await dns.asyncquery.udp_with_fallback(
        q=dns.message.make_query(query, getattr(dns.rdatatype, types)),
        where=server)
    return r[0]


@Client.on_message(filters.command('dig') & filters.create(cmd_help))
async def doh(client: Bot, message: Message):
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)
    start = time.time()
    result = await dig_query(args.server, args.query, args.type.upper())
    end = (time.time() - start)*1000
    text = ''
    opt = client.config
    if opt.slave.enable:
        text += '🔍 子節點查詢結果:\n\n'
        text += '📍 <code>{name} ({region})</code>\n<code>{ip}（{asn}）</code>\n\n'.format(
            name=escape(opt.slave.name),
            ip=client.slave.ip,
            asn=escape(client.slave.asn),
            region=escape(client.slave.region)
        )
    else:
        text += '🔍 查詢結果:\n'
    if args.raw:
        text += '<code>{result}</code>\n\n'.format(result=escape(result.to_text()))
    else:
        for i in result.answer:
            text += '<code>{result}</code>\n\n'.format(result=escape(i.to_text()))

    if not args.benchmark:
        text += '⏳ 快樂錶: {cons}'.format(cons=f'{round(end/1000, 2)}s' if end >= 1000 else f'{round(end, 2)}ms')
    else:
        text += '🏁 測試結果: \n'
        average = 0.0
        for i in range(1, args.benchmark + 1):
            start = time.time()
            await dig_query(args.server, args.query, args.type.upper())
            end = (time.time() - start) * 1000
            average += end
            text += '{t}. - <code>{cons}</code>\n'.format(
                t=i,
                cons=f'{round(end / 1000, 2)}s' if end >= 1000 else f'{round(end, 2)}ms'
            )
        a_ = round(average / args.benchmark, 3)
        text += '\n🤌 平均: <code>{average}</code>'.format(
            average=f'{round(a_ / 1000, 2)}s' if a_ >= 1000 else f'{round(a_, 2)}ms')
    await message.reply_text(text)
