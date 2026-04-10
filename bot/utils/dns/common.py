from __future__ import annotations

import dns.message
import dns.rcode
import dns.rdatatype


def parse_rdataset(msg: dns.message.Message) -> list[dict]:
    """Parse all answer/authority/additional records into a list of dicts."""
    records = []
    for section_name, section in [
        ("answer", msg.answer),
        ("authority", msg.authority),
        ("additional", msg.additional),
    ]:
        for rrset in section:
            rdtype = dns.rdatatype.to_text(rrset.rdtype)
            for rdata in rrset:
                records.append(
                    {
                        "section": section_name,
                        "name": str(rrset.name),
                        "type": rdtype,
                        "ttl": rrset.ttl,
                        "data": rdata.to_text(),
                    }
                )
    return records


def format_records(msg: dns.message.Message) -> str:
    """Return a compact human-readable string of DNS records."""
    records = parse_rdataset(msg)
    if not records:
        rcode = dns.rcode.to_text(msg.rcode())
        return f"(no records, rcode={rcode})"
    lines = []
    for r in records:
        lines.append(f"{r['name']} {r['ttl']} {r['type']} {r['data']}")
    return "\n".join(lines)


def format_response(
    msg: dns.message.Message, elapsed_ms: float, raw: bool = False
) -> str:
    """Format a DNS response for display in Telegram."""
    rcode = dns.rcode.to_text(msg.rcode())
    if raw:
        return f"<pre>{msg.to_text()}</pre>\n⏱ {elapsed_ms:.2f} ms"

    lines = [f"rcode: <b>{rcode}</b>  ⏱ <b>{elapsed_ms:.2f} ms</b>"]
    records = parse_rdataset(msg)
    if records:
        for r in records:
            lines.append(f"  {r['type']} {r['data']}  <i>TTL {r['ttl']}</i>")
    else:
        lines.append("  (no records)")
    return "\n".join(lines)
