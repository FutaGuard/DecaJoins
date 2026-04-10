from __future__ import annotations

import time

import httpx

import dns.asyncquery
import dns.message
import dns.rdatatype


async def query_doh(
    server_url: str,
    domain: str,
    record_type: str,
    timeout: float = 5.0,
) -> tuple[dns.message.Message, float]:
    """Query a DNS-over-HTTPS server."""
    qtype = dns.rdatatype.from_text(record_type)
    msg = dns.message.make_query(domain, qtype)

    t0 = time.perf_counter()
    async with httpx.AsyncClient(verify=True) as session:
        response = await dns.asyncquery.https(
            msg,
            server_url,
            client=session,
            timeout=timeout,
        )
    elapsed = (time.perf_counter() - t0) * 1000
    return response, elapsed
