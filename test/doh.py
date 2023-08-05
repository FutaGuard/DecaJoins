import dns.message
import dns.query
import dns.rdatatype
import dns.asyncquery
import asyncio
import httpx

async def main():
    where = 'https://doh.futa.gg/dns-query'
    qname = 'google.com'
    s = httpx.AsyncClient()
    async with s as client:
        q = dns.message.make_query(qname, dns.rdatatype.A)
        r = await dns.asyncquery.https(q, where, client=client)
        # r = dns.query.https(q, where, session=client)
        # for answer in r.answer:
        f = r.to_text()
        print(f)


if __name__ == '__main__':
    asyncio.run(main())
