from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command('start'))
async def start(_, message: Message):
    text = '使用方法如下\n' \
           '/doh -s <doh 伺服器 網域> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n' \
           '範例： /doh -s https://doh.futa.gg/dns-query -q google.com -t A\n' \
           '/dig -s <dns 伺服器 ip> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n' \
           '範例： /dig -s 1.1.1.1 -q google.com -t NS -b 5\n' \
           '/doq -s <doq 伺服器 網域> -q <查詢網域> -p <連接埠> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n'
    await message.reply_text(text)