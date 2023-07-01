import asyncio

# import trio

import dns.asyncresolver
import dns.message
import dns
import asyncio


async def main():
    msg = dns.message.make_query(qname='google.com', rdtype='A')
    r = await dns.asyncquery.udp(q=msg, where='1.1.1.1')
    print(r.answer[0].to_text().split(' ')[-1])


if __name__ == '__main__':
    asyncio.run(main())
