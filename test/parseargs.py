import argparse
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Args:
    server: Optional[str] = field(metadata=config(field_name='s'))
    query: Optional[str] = field(metadata=config(field_name='q'))
    type: Optional[str] = field(metadata=config(field_name='t'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        nargs='*',
        type=str,
        help='some doh',
        required=False,
        default='https://doh.futa.gg/dns-query',
    )
    parser.add_argument('-q', nargs='*', type=str, help='some domain', required=False)
    parser.add_argument(
        '-t', nargs='*', type=str, help='some type', required=False, default='A'
    )

    strings = ""
    args = parser.parse_args(strings.split())
    # my_args = Args(**vars(args))
    # print(my_args)
    r = Args.from_dict(vars(args))
    print(r)

    # print(args)
