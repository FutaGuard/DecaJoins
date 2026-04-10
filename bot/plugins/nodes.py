from __future__ import annotations

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot.config import get_config
from bot.node.manager import manager
from bot.node.models import NodeStatus


@Client.on_message(filters.command("nodes"))
async def cmd_nodes(client: Client, message: Message):
    config = get_config()
    if config.node.mode == "standalone":
        await message.reply_text(
            "ℹ️ 目前為單機模式，未啟用多節點功能。", parse_mode=ParseMode.HTML
        )
        return

    nodes = manager.get_nodes()
    if not nodes:
        await message.reply_text(
            "📭 目前沒有任何已註冊的節點。", parse_mode=ParseMode.HTML
        )
        return

    lines = ["🖥 <b>節點狀態</b>\n"]
    for node in nodes:
        icon = "🟢" if node.status == NodeStatus.ONLINE else "🔴"
        last_hb = node.last_heartbeat.strftime("%H:%M:%S")
        lines.append(
            f"{icon} <b>{node.name}</b>\n"
            f"   IP: <code>{node.ip}</code>\n"
            f"   最後心跳: {last_hb}"
        )
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
