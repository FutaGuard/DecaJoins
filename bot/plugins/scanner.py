# /scan https://doh.futa.gg/dns-query
# WOT -> Result
# Google SafeBrowsing -> Result
# Microsoft SmartScreen -> Result
# ReScan.pro -> Result
# from aiohttp import ClientSession
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types import Message

from bot.utils.validators import is_url

# /urlscan https://doh.futa.gg/dns-query

# async def check_cmd(_, __, message: Message):


@Client.on_message(
    filters.command('urlscan', prefixes='/') # pyright: ignore [reportGeneralTypeIssues]
)
async def urlscan(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text('缺少參數')
    if not is_url(message.text.split(' ')[1]):
        return await message.reply_text('URL 格式錯誤')

    await message.reply_text(f'正在掃描中...\n🔗 URL：{message.command[1]}')
