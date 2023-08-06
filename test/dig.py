import asyncio

import dns

# import trio
import dns.asyncquery
import dns.message


async def main():
    msg = dns.message.make_query(qname='bgp.co', rdtype='TXT')
    r = await dns.asyncquery.udp_with_fallback(q=msg, where='216.218.130.2')
    # print(r.answer[0].to_text().split(' ')[-1])
    print(r[0])


if __name__ == '__main__':
    asyncio.run(main())
