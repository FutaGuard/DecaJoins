from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types import Message

from bot.consts import BOT_DESCRIPTION


@Client.on_message(
    filters.command('start')  # pyright: ignore [reportGeneralTypeIssues]
)
async def start(_, message: Message):
    await message.reply_text(BOT_DESCRIPTION, disable_web_page_preview=True)
