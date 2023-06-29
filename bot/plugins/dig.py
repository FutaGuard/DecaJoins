from typing import List, Optional

from pyrogram import Client, filters
from pyrogram.types import Message
import argparse
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json
import validators


@dataclass_json
@dataclass
class Args:
    server: Optional[str] = field(metadata=config(field_name='s'))
    query: Optional[str] = field(metadata=config(field_name='q'))
    type: Optional[str] = field(metadata=config(field_name='t'))

def parse_args(string: List[str]) -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', nargs='*', type=str, help='some doh', required=False,
                        default='https://doh.futa.gg/dns-query')
    parser.add_argument('-q', nargs='*', type=str, help='some domain', required=False)
    parser.add_argument('-t', nargs='*', type=str, help='some type', required=False, default='A')
    return Args.from_dict(vars(parser.parse_args(string)))

def cmd_help(_, __, message: Message):
    # /doh -s https://doh.futa.gg/dns-query -q google.com -t A
    # message.
    cmd = message.text.split(' ')[1:]
    args = parse_args(cmd)
    text = '使用方式: /doh -s <doh> -q <domain> -t <type>\n'

    if not args.query:
        text += '缺少 -q 參數\n'

    if args.type.upper() not in ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'SRV', 'TXT']:
        text += '-t type 參數錯誤'

    if validators.url(args.server):
        text += '-s DoH 伺服器格式錯誤'

    if validators.url(args.query):
        text += '-q query 網域格式錯誤'
