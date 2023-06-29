from typing import List, Optional

from pyrogram import Client, filters
from pyrogram.types import Message
import argparse
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json
import validators
import dns.message
import dns.query
import dns.rdatatype
import requests
from html import escape


@dataclass_json
@dataclass
class Args:
    server: Optional[str] = field(metadata=config(field_name='s'))
    query: Optional[str] = field(metadata=config(field_name='q'))
    type: Optional[str] = field(metadata=config(field_name='t'))


def parse_args(string: List[str]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', type=str, help='some doh', required=False,
                        default='https://doh.futa.gg/dns-query')
    parser.add_argument('-q', type=str, help='some domain', required=False)
    parser.add_argument('-t', type=str, help='some type', required=False, default='A')
    return Args.from_dict(vars(parser.parse_args(string)))


async def cmd_help(_, __, message: Message):
    # /doh -s https://doh.futa.gg/dns-query -q google.com -t A
    # message.
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)

    text = '使用方式: /doh -s <doh> -q <domain> -t <type>\n'
    pass_flag = True

    if not args.query:
        text += '缺少 -q 參數\n'
        pass_flag = False

    if args.type.upper() not in ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'SRV', 'TXT']:
        text += '-t type 參數錯誤\n'
        pass_flag = False

    if not validators.url(args.server):
        text += '-s DoH 伺服器格式錯誤\n'
        pass_flag = False

    if validators.url(args.query):
        text += '-q query 網域格式錯誤\n'
        pass_flag = False

    if not pass_flag:
        await message.reply_text(text)
        return False
    return True


async def doh_query(server: str, query: str, types: str) -> dns.message.Message:
    s = requests.Session()
    with s as client:
        return dns.query.https(
            q=dns.message.make_query(query, getattr(dns.rdatatype, types)),
            where=server,
            session=client)


@Client.on_message(filters.command('doh') & filters.create(cmd_help))
async def doh(client: Client, message: Message):
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)
    result = await doh_query(args.server, args.query, args.type.upper())
    text = '🔍 查詢結果:\n' \
           '<code>{}</code>\n'.format(escape(result.to_text()))
    await message.reply_text(text)
