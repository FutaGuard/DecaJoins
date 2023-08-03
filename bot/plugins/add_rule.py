import argparse

from time import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os.path
from html import escape


@Client.on_message(filters.command('add_rule', prefixes='/'))
async def add_rule(_, message: Message):
    # add hosts
    cmd = message.text.split(' ', 2)
    if len(cmd) != 3:
        return await message.reply_text('缺少參數\n/add_rule <file_name> <rule>')

    filename = cmd[1] + '.txt'
    if not os.path.exists(filename):
        return await message.reply_text(f'{filename} 檔案不存在')

    tmp = str(int(time()))
    with open(f'/tmp/{tmp}.txt', 'w') as f:
        f.write(cmd[2])
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton('✅', callback_data=f'add_rule {filename} {tmp}'),
    ]])
    text = '確定要新增下列規則嗎？\n' \
           '<code>{r}</code>'.format(r=escape(cmd[2]))
    await message.reply_text(text, reply_markup=kb)
