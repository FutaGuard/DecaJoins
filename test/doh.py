import requests

import dns.message
import dns.query
import dns.rdatatype


def main():
    where = 'https://doh.futa.gg/dns-query'
    qname = 'google.com'
    s = requests.Session()
    with s as client:
        q = dns.message.make_query(qname, dns.rdatatype.A)
        r = dns.query.https(q, where, session=client)
        # for answer in r.answer:
        f = r.to_text()
        print(f)


if __name__ == '__main__':
    main()
