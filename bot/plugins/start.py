from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command('start'))
async def start(_, message: Message):
    text = '這個機器人可以幫助你快速查 UDP, DoH, DoQ 紀錄，同時帶有其他特點：\n' \
           '1. 查詢時帶有時間功能，提供直覺的方式了解節點品質\n' \
           '2. 可快速批量查詢，可對單一節點連續高達 30 次查詢並統計平均速度\n' \
           '3. 更多功能敬請期待\n\n'
    text += '📝 使用方法如下\n' \
            '/doh -s <doh 伺服器 網域> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n' \
            '範例： /doh -s https://doh.futa.gg/dns-query -q google.com -t A\n\n' \
            '/dig -s <dns 伺服器 ip> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n' \
            '範例： /dig -s 1.1.1.1 -q google.com -t NS -b 5\n\n' \
            '/doq -s <doq 伺服器 網域> -q <查詢網域> -p <連接埠> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>\n\n'
    text += '🥸 隱私聲明\n' \
            '本機器人運作時並不會以任何形式記錄你的查詢，但不包含網路提供商，若因使用本機器人查詢造成您有任何損失\n' \
            '作者不付任何責任，如有疑慮請立即封鎖本機器人\n\n'
    text += '⚡ 關於作者\n' \
            '作者是 @kachowlife 並獨立經營 @FutaGuard 頻道，如果喜歡的話不妨點及追蹤，同時本機器人所有原始碼均開源在 https://github.com/FutaGuard/DecaJoins\n' \
            '喜歡的話歡迎也對 Repo 點擊 ⭐ Star，同時推薦你到 https://service.futa.gg 看更多好玩的東西'
    await message.reply_text(text, disable_web_page_preview=True)