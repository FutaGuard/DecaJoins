# /scan https://doh.futa.gg/dns-query
# WOT -> Result
# Google SafeBrowsing -> Result
# Microsoft SmartScreen -> Result
# ReScan.pro -> Result
from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message

import validators
# /urlscan https://doh.futa.gg/dns-query

# async def check_cmd(_, __, message: Message):


@Client.on_message(filters.command('urlscan', prefixes='/'))
async def urlscan(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text('缺少參數')
    if not validators.url(message.text.split(' ')[1]):
        return await message.reply_text('URL 格式錯誤')

    sent = await message.reply_text(f'正在掃描中...\n🔗 URL：{message.command[1]}')
