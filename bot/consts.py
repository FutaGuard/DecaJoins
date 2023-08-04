BOT_DESCRIPTION = '''\
這個機器人可以幫助你快速查 UDP, DoH, DoQ 紀錄，同時帶有其他特點：
1. 查詢時帶有時間功能，提供直覺的方式了解節點品質
2. 可快速批量查詢，可對單一節點連續高達 30 次查詢並統計平均速度
3. 更多功能敬請期待

📝 使用方法如下
/doh -s <doh 伺服器 網域> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>
範例： /doh -s https://doh.futa.gg/dns-query -q google.com -t A

/dig -s <dns 伺服器 ip> -q <查詢網域> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>
範例： /dig -s 1.1.1.1 -q google.com -t NS -b 5

/doq -s <doq 伺服器 網域> -q <查詢網域> -p <連接埠> -t <查詢類型> -b <測速> -R <留空表示輸出原始內容，不輸入則簡短輸出>

🥸 隱私聲明
本機器人運作時並不會以任何形式記錄你的查詢，但不包含網路提供商，若因使用本機器人查詢造成您有任何損失
作者不付任何責任，如有疑慮請立即封鎖本機器人

⚡ 關於作者
作者是 @kachowlife 並獨立經營 @FutaGuard 頻道，如果喜歡的話不妨點及追蹤，同時本機器人所有原始碼均開源在 https://github.com/FutaGuard/DecaJoins
喜歡的話歡迎也對 Repo 點擊 ⭐ Star，同時推薦你到 https://service.futa.gg 看更多好玩的東西\
'''

SUPPORTED_DNS_TYPES = frozenset(
    ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'SRV', 'TXT', 'ANY']
)
