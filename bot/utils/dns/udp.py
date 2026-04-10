from __future__ import annotations

import time

import dns.asyncquery
import dns.message
import dns.rdatatype


async def query_udp(
    server_ip: str,
    domain: str,
    record_type: str,
    port: int = 53,
    timeout: float = 5.0,
) -> tuple[dns.message.Message, float]:
    """Query a DNS server over plain UDP.

    Args:
        server_ip:   IP address (or hostname) of the DNS resolver.
        domain:      The domain name to query.
        record_type: DNS record type string, e.g. ``"A"``, ``"AAAA"``, ``"MX"``.
        port:        UDP port to use (default 53).
        timeout:     Socket timeout in seconds (default 5.0).

    Returns:
        A ``(response, elapsed_ms)`` tuple where *response* is the parsed
        :class:`dns.message.Message` and *elapsed_ms* is the round-trip time
        in milliseconds as a :class:`float`.

    Raises:
        dns.exception.Timeout: If the query times out.
        dns.exception.DNSException: On any other dnspython-level error.
    """
    qtype = dns.rdatatype.from_text(record_type)
    msg = dns.message.make_query(domain, qtype)

    t0 = time.perf_counter()
    response = await dns.asyncquery.udp(msg, server_ip, port=port, timeout=timeout)
    elapsed = (time.perf_counter() - t0) * 1000

    return response, elapsed
