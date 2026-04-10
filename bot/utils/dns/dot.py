from __future__ import annotations

import asyncio
import socket
import time

import dns.asyncquery
import dns.inet
import dns.message
import dns.rdatatype


def _is_ip(addr: str) -> bool:
    try:
        dns.inet.af_for_address(addr)
        return True
    except ValueError:
        return False


async def query_dot(
    server: str,
    domain: str,
    record_type: str,
    port: int = 853,
    timeout: float = 5.0,
) -> tuple[dns.message.Message, float]:
    """Query a DNS-over-TLS server.

    *server* may be either a hostname (e.g. ``dns.google``) or an IP address.
    When a hostname is supplied it is resolved to an IP via the OS resolver and
    passed as *server_hostname* so that TLS SNI / certificate verification still
    works correctly.
    """
    if _is_ip(server):
        ip = server
        server_hostname: str | None = None
    else:
        loop = asyncio.get_event_loop()
        infos = await loop.getaddrinfo(server, port, type=socket.SOCK_STREAM)
        if not infos:
            raise OSError(f"Could not resolve hostname: {server}")
        ip = infos[0][4][0]
        server_hostname = server

    qtype = dns.rdatatype.from_text(record_type)
    msg = dns.message.make_query(domain, qtype)

    t0 = time.perf_counter()
    response = await dns.asyncquery.tls(
        msg,
        ip,
        port=port,
        timeout=timeout,
        server_hostname=server_hostname,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return response, elapsed
