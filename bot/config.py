import logging
import os
import sys
from dataclasses import dataclass, field

import coloredlogs
from dataclasses_json import dataclass_json
from yaml import safe_load
from yaml.error import Mark, YAMLError, MarkedYAMLError

logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)


@dataclass_json
@dataclass
class Config:
    @dataclass_json
    @dataclass
    class Bot:
        bot_token: str = field(hash=False, repr=True, compare=False, default=None)
        api_id: str = field(hash=False, repr=True, compare=False, default=None)
        api_hash: str = field(hash=False, repr=True, compare=False, default=None)

    @dataclass_json
    @dataclass
    class Log:
        level: str = field(hash=False, repr=True, compare=False, default=None)

    @dataclass_json
    @dataclass
    class Proxy:
        tw_http: str = field(hash=False, repr=True, compare=False, default=None)
        tw_https: str = field(hash=False, repr=True, compare=False, default=None)

    dev_mode: bool = field(hash=False, repr=True, compare=False, default=None)
    bot: Bot = Bot
    log: Log = Log
    admin: int = 5440674042
    proxy: Proxy = Proxy


def load(initial: bool = False):
    """
    讀取設定用的東西
    usage: bot.config.loads()
    tpyes: config 自己找找
    """
    filename = 'env_config.yml'
    if not os.path.isfile(f'./{filename}'):
        logger.critical('找不到 env_config.yml')
        sys.exit(1)

    with open(f'./{filename}', mode='r', encoding='utf8') as f:
        try:
            loads = safe_load(f.read())
        except (Mark, YAMLError, MarkedYAMLError):
            logger.critical('解讀 env_config.yml 錯誤')
            sys.exit(1)
        else:
            # check if set dev mode true.
            if loads['dev_mode']:
                if initial:
                    logger.warning('Set to Development mode.')
                if not os.path.isfile(f'./dev_{filename}'):
                    logger.critical('找不到 dev_env_config.yml')
                    sys.exit(1)
                with open(f'./dev_{filename}', mode='r', encoding='utf8') as f_dev:
                    try:
                        loads = safe_load(f_dev.read())
                    except (Mark, YAMLError, MarkedYAMLError):
                        logger.critical('解讀 dev_env_config.yml 錯誤')
                        sys.exit(1)
                    else:
                        opts: Config = Config.from_dict(loads)
                        return opts
            opts: Config = Config.from_dict(loads)
            os.environ['http_proxy'] = opts.proxy.http
            os.environ['https_proxy'] = opts.proxy.https
            return opts
