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
import dns.asyncquery
import time
from html import escape
import dns.asyncquery
import httpx


class ArgumentParser(argparse.ArgumentParser):
    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.
        If only it were made available in the ArgumentError object. It is
        passed as it's first arg...
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if '/'.join(action.option_strings) == name:
                return action
            elif action.metavar == name:
                return action
            elif action.dest == name:
                return action

    def error(self, message):
        pass


@dataclass_json
@dataclass
class Args:
    server: Optional[str] = field(metadata=config(field_name='s'))
    query: Optional[str] = field(metadata=config(field_name='q'))
    type: Optional[str] = field(metadata=config(field_name='t'))


def parse_args(string: List[str]) -> Args:
    parser = ArgumentParser()
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
    # s = requests.Session()
    async with httpx.AsyncClient() as client:
        return await dns.asyncquery.https(
            q=dns.message.make_query(query, getattr(dns.rdatatype, types)),
            where=server,
            client=client)


@Client.on_message(filters.command('doh') & filters.create(cmd_help))
async def doh(_, message: Message):
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)
    start = time.time()
    result = await doh_query(args.server, args.query, args.type.upper())
    end = round(time.time() - start, 2)
    text = '🔍 查詢結果:\n' \
           '<code>{result}</code>\n\n' \
           '⏳ 耗時: {cons}'.format(result=escape(result.to_text()),
                                   cons=f'{end}s' if end >= 1000 else f'{end * 1000}ms')
    await message.reply_text(text)
