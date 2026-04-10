from __future__ import annotations

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot.config import get_config
from bot.node.manager import manager
from bot.node.models import DNSQueryType, Task, TaskResultRequest
from bot.utils.dns import parse_rdataset, query_doq

from .common import (
    build_benchmark_result,
    build_local_result,
    build_result_header,
    format_node_results,
    missing_args_text,
    parse_args,
)

PROTO = "DOQ"
EXAMPLE_SERVER = "dns.adguard.com"


@Client.on_message(filters.command("doq"))
async def cmd_doq(client: Client, message: Message):
    raw_text = message.text or ""
    parts = raw_text.split(None, 1)
    arg_str = parts[1] if len(parts) > 1 else ""
    args = parse_args(arg_str)

    if not args.server or not args.query:
        await message.reply_text(
            missing_args_text(PROTO, EXAMPLE_SERVER), parse_mode=ParseMode.HTML
        )
        return

    port = args.port or 853
    config = get_config()
    header = build_result_header(PROTO, args.server, args.query, args.record_type)

    # ── benchmark mode ────────────────────────────────────────────────────────
    if args.benchmark > 0:
        msg = await message.reply_text(
            f"{header}⏳ 測速中 (0/{args.benchmark})…", parse_mode=ParseMode.HTML
        )
        timings: list[float] = []
        last_resp = None
        for i in range(args.benchmark):
            try:
                resp, elapsed = await query_doq(
                    args.server, args.query, args.record_type, port=port
                )
                timings.append(elapsed)
                last_resp = resp
            except Exception:
                timings.append(0.0)
            await msg.edit_text(
                f"{header}⏳ 測速中 ({i + 1}/{args.benchmark})…",
                parse_mode=ParseMode.HTML,
            )
        valid = [t for t in timings if t > 0]
        if last_resp and valid:
            text = build_benchmark_result(
                PROTO,
                args.server,
                args.query,
                args.record_type,
                valid,
                last_resp,
                args.raw,
            )
            await msg.edit_text(text, parse_mode=ParseMode.HTML)
        return

    # ── host multi-node mode ──────────────────────────────────────────────────
    online = manager.get_online_nodes() if config.node.mode == "host" else []
    if config.node.mode == "host" and online:
        task = Task(
            type=DNSQueryType.DOQ,
            server=args.server,
            query=args.query,
            record_type=args.record_type,
            chat_id=message.chat.id if message.chat else None,
        )
        manager.create_task(task)

        init_text = (
            header
            + f"⏳ 等待 {len(task.target_nodes)} 個節點回應…\n"
            + f"節點：{', '.join(task.target_nodes)}"
        )
        sent = await message.reply_text(init_text, parse_mode=ParseMode.HTML)
        assert sent is not None
        task.message_id = sent.id

        # Execute locally as host node
        try:
            resp, elapsed = await query_doq(
                args.server, args.query, args.record_type, port=port
            )
            records = parse_rdataset(resp)
            manager.submit_result(
                task.id,
                "host",
                TaskResultRequest(success=True, result=records, elapsed_ms=elapsed),
            )
        except Exception as e:
            manager.submit_result(
                task.id,
                "host",
                TaskResultRequest(success=False, error=str(e), elapsed_ms=0.0),
            )

        async def on_result(t, result):
            results = manager.get_results(t.id)
            responded = len(t.client)
            total = len(t.target_nodes)
            body = format_node_results(results)
            status = (
                f"✅ {responded}/{total} 節點已回應"
                if responded < total
                else f"✅ 全部 {total} 個節點已回應"
            )
            if sent is not None:
                await sent.edit_text(
                    header + status + "\n" + body, parse_mode=ParseMode.HTML
                )

        manager.register_result_callback(task.id, on_result)
        return

    # ── standalone mode ───────────────────────────────────────────────────────
    msg = await message.reply_text(header + "⏳ 查詢中…", parse_mode=ParseMode.HTML)
    try:
        resp, elapsed = await query_doq(
            args.server, args.query, args.record_type, port=port
        )
        text = build_local_result(resp, elapsed, args.raw)
        await msg.edit_text(header + text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(
            header + f"❌ 查詢失敗：<code>{e}</code>", parse_mode=ParseMode.HTML
        )
