from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Bot


def get_elapsed_info(elapsed: float):
    return f'{round(elapsed/1e3, 2)}s' if elapsed >= 1e3 else f'{round(elapsed, 2)}ms'


def has_standby(client: "Bot"):
    return client.config.slave.enable and client.slave


def get_standby_info(client: "Bot"):
    if has_standby(client):
        assert client.slave
        name = escape(client.config.slave.name or '')
        ip = client.slave.ip
        asn = escape(client.slave.asn)
        region = escape(client.slave.region)
        return f'''\
📍 <code>{name} ({region})</code>
<code>{ip}（{asn}）</code>
'''
    return ''
