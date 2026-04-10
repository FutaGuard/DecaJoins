from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Optional

import dns.message
from bot.consts import SUPPORTED_DNS_TYPES
from bot.utils.dns.common import format_response


@dataclass
class DnsArgs:
    server: Optional[str] = None
    query: Optional[str] = None
    record_type: str = "A"
    benchmark: int = 0  # 0 = no benchmark
    raw: bool = False
    port: Optional[int] = None


def parse_args(text: str) -> DnsArgs:
    """Parse a DNS command argument string into DnsArgs."""
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()

    args = DnsArgs()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "-s" and i + 1 < len(tokens):
            args.server = tokens[i + 1]
            i += 2
        elif t == "-q" and i + 1 < len(tokens):
            args.query = tokens[i + 1]
            i += 2
        elif t == "-t" and i + 1 < len(tokens):
            rtype = tokens[i + 1].upper()
            args.record_type = rtype if rtype in SUPPORTED_DNS_TYPES else "A"
            i += 2
        elif t == "-b" and i + 1 < len(tokens):
            try:
                args.benchmark = min(int(tokens[i + 1]), 30)
            except ValueError:
                args.benchmark = 1
            i += 2
        elif t == "-p" and i + 1 < len(tokens):
            try:
                args.port = int(tokens[i + 1])
            except ValueError:
                pass
            i += 2
        elif t == "-R":
            args.raw = True
            i += 1
        else:
            i += 1
    return args


def missing_args_text(proto: str, example_server: str) -> str:
    return (
        f"❌ 缺少必要參數\n\n"
        f"<b>用法：</b>\n"
        f"<code>/{proto.lower()} -s {example_server} -q google.com -t A</code>\n\n"
        f"<b>參數說明：</b>\n"
        f"  <code>-s</code>  伺服器地址\n"
        f"  <code>-q</code>  查詢網域\n"
        f"  <code>-t</code>  紀錄類型（預設 A）\n"
        f"  <code>-b N</code>  測速 N 次（最多 30）\n"
        f"  <code>-p</code>  連接埠\n"
        f"  <code>-R</code>  原始輸出\n"
    )


def build_result_header(proto: str, server: str, query: str, record_type: str) -> str:
    return (
        f"🔍 <b>{proto}</b>  <code>{query}</code>  {record_type}\n"
        f"📡 <code>{server}</code>\n"
        f"{'─=' * 5}\n"
    )


def build_local_result(msg: dns.message.Message, elapsed_ms: float, raw: bool) -> str:
    return format_response(msg, elapsed_ms, raw=raw)


def build_benchmark_result(
    proto: str,
    server: str,
    query: str,
    record_type: str,
    timings: list[float],
    last_msg: dns.message.Message,
    raw: bool,
) -> str:
    header = build_result_header(proto, server, query, record_type)
    mn, mx, avg = min(timings), max(timings), sum(timings) / len(timings)
    stats = (
        f"📊 <b>測速</b> {len(timings)} 次\n"
        f"  最快 {mn:.2f} ms  最慢 {mx:.2f} ms  平均 {avg:.2f} ms\n"
    )
    last = build_local_result(last_msg, timings[-1], raw)
    return header + stats + last


def format_node_results(results: list) -> str:
    """Format multi-node TaskResult list for Telegram HTML."""
    lines = []
    for r in results:
        status = "✅" if r.success else "❌"
        lines.append(f"{status} <b>{r.node_name}</b>  ⏱ {r.elapsed_ms:.2f} ms")
        if r.success and r.result:
            if isinstance(r.result, list):
                for rec in r.result[:5]:
                    if isinstance(rec, dict):
                        lines.append(
                            f"  {rec.get('type', '')} {rec.get('data', '')}"
                            f"  <i>TTL {rec.get('ttl', '')}</i>"
                        )
                    else:
                        lines.append(f"  {rec}")
            else:
                lines.append(f"  {str(r.result)[:200]}")
        elif r.error:
            lines.append(f"  ⚠️ {r.error}")
    return "\n".join(lines)
