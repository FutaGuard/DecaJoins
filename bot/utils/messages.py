from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Bot


def get_elapsed_info(elapsed: float):
    return f'{round(elapsed/1e3, 2)}s' if elapsed >= 1e3 else f'{round(elapsed, 2)}ms'


def has_standby(client: "Bot"):
    return client.config.standby.enable and client.standby


def get_standby_info(client: "Bot"):
    if has_standby(client):
        assert client.standby
        name = escape(client.config.standby.name or '')
        ip = client.standby.ip
        asn = escape(client.standby.asn_org)
        region = escape(client.standby.country)
        return f'''\
📍 <code>{name} ({region})</code>
<code>{ip}（{asn}）</code>
'''
    return ''
