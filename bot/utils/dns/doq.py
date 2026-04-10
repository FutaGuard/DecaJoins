from __future__ import annotations

import asyncio
import socket
import time

import dns.asyncquery
import dns.message
import dns.rdatatype


def _is_ip(address: str) -> bool:
    """Return True if address is a numeric IP (v4 or v6)."""
    try:
        socket.inet_pton(socket.AF_INET, address)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, address)
        return True
    except OSError:
        pass
    return False


async def query_doq(
    server: str,
    domain: str,
    record_type: str,
    port: int = 853,
    timeout: float = 5.0,
) -> tuple[dns.message.Message, float]:
    """Query a DNS-over-QUIC server.

    ``server`` may be a hostname or an IP address.  When a hostname is given it
    is resolved to an IP via :func:`asyncio.get_event_loop().getaddrinfo` and
    the original hostname is forwarded as *server_hostname* so that QUIC/TLS
    SNI and certificate verification work correctly.
    """
    if _is_ip(server):
        ip = server
        server_hostname: str | None = None
    else:
        loop = asyncio.get_event_loop()
        infos = await loop.getaddrinfo(server, port, type=socket.SOCK_DGRAM)
        if not infos:
            raise OSError(f"Could not resolve hostname: {server!r}")
        ip = infos[0][4][0]
        server_hostname = server

    qtype = dns.rdatatype.from_text(record_type)
    msg = dns.message.make_query(domain, qtype)

    t0 = time.perf_counter()
    response = await dns.asyncquery.quic(
        msg,
        ip,
        port=port,
        timeout=timeout,
        server_hostname=server_hostname,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return response, elapsed
