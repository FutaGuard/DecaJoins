import dns
import dns.message
import dns.asyncquery
import asyncio


async def main():
    qname = 'google.com'
    q = dns.message.make_query(qname, dns.rdatatype.A)
    r = await dns.asyncquery.quic(q, '94.140.14.140', port=853, connection=None, verify=False)
    print(r.to_text())

if __name__ == '__main__':
    asyncio.run(main())
