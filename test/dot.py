import requests

import dns.message
import dns.query
import dns.rdatatype


def main():
    where = 'tls://dns.google:853'
    qname = 'google.com'

    q = dns.message.make_query(qname, dns.rdatatype.A)
    r = dns.query.tls(q, where)
    print(r)


if __name__ == '__main__':
    main()
