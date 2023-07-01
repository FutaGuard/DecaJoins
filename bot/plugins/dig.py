import argparse
import time
from dataclasses import dataclass, field
from html import escape
from typing import List, Optional

import dns.asyncquery
import dns.message
import dns.query
import dns.rdatatype
import validators
from dataclasses_json import config, dataclass_json
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils import ArgumentParser


@dataclass_json
@dataclass
class Args:
    server: Optional[str] = field(metadata=config(field_name='s'))
    query: Optional[str] = field(metadata=config(field_name='q'))
    type: Optional[str] = field(metadata=config(field_name='t'))
    benchmark: Optional[int] = field(metadata=config(field_name='b'))
    raw: Optional[bool] = field(metadata=config(field_name='R'))


def parse_args(string: List[str]) -> Args:
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, help='some server', required=False,
                        default='https://doh.futa.gg/dns-query')
    parser.add_argument('-q', type=str, help='some domain', required=False)
    parser.add_argument('-t', type=str, help='some type', required=False, default='A')
    parser.add_argument('-b', type=int, help='benchmark', required=False, default=None)
    parser.add_argument('-R', type=bool, help='raw', required=False, default=False,
                        action=argparse.BooleanOptionalAction)
    return Args.from_dict(vars(parser.parse_args(string)))


async def cmd_help(_, __, message: Message):
    # /doh -s https://doh.futa.gg/dns-query -q google.com -t A
    # message.
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)

    text = '使用方式: /dig -s <udp ip> -q <domain> -t <type>\n'
    pass_flag = True

    if not args.query:
        text += '缺少 -q 參數\n'
        pass_flag = False
    else:
        if validators.url(args.query):
            text += '-q query 網域格式錯誤\n'
            pass_flag = False

    if args.type.upper() not in ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'SRV', 'TXT']:
        text += '-t type 參數錯誤\n'
        pass_flag = False

    if validators.ipv4(args.server) or validators.ipv6(args.server):
        pass
    else:
        text += '-s UDP IP 伺服器格式錯誤\n'
        pass_flag = False

    if args.benchmark and not validators.between(int(args.benchmark), min=2, max=30):
        text += '-b benchmark 次數設定錯誤\n'
        pass_flag = False

    if not pass_flag:
        await message.reply_text(text)
        return False
    return True


async def dig_query(server: str, query: str, types: str) -> dns.message.Message:
    return await dns.asyncquery.udp(
        q=dns.message.make_query(query, getattr(dns.rdatatype, types)),
        where=server)


@Client.on_message(filters.command('dig') & filters.create(cmd_help))
async def doh(_, message: Message):
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)
    start = time.time()
    result = await dig_query(args.server, args.query, args.type.upper())
    end = round(time.time() - start, 2)
    text = '🔍 查詢結果:\n'
    if args.raw:
        text += '<code>{result}</code>\n\n'.format(result=escape(result.to_text()))
    else:
        for i in result.answer:
            text += '<code>{result}</code>\n\n'.format(result=escape(i.to_text()))

    if not args.benchmark:
        text += '⏳ 快樂錶: {cons}'.format(cons=f'{end}s' if end >= 1000 else f'{end * 1000}ms')
    else:
        text += '🏁 測試結果: \n'
        average = 0.0
        for i in range(1, args.benchmark + 1):
            start = time.time()
            await dig_query(args.server, args.query, args.type.upper())
            end = round(time.time() - start, 2)
            average += end
            text += '{t}. - <code>{cons}</code>\n'.format(
                t=i,
                cons=f'{end}s' if end >= 1000 else f'{end * 1000}ms'
            )
        a_ = round(average / args.benchmark, 3)
        text += '\n🤌 平均: <code>{average}</code>'.format(average=f'{a_}s' if a_ >= 1000 else f'{a_ * 1000}ms')
    await message.reply_text(text)
