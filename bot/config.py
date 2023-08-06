import logging
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

import coloredlogs
from dataclasses_json import DataClassJsonMixin
from yaml import safe_load
from yaml.error import MarkedYAMLError, YAMLError

logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)


@dataclass
class Config(DataClassJsonMixin):
    @dataclass
    class Bot(DataClassJsonMixin):
        bot_token: Optional[str] = field(
            hash=False, repr=True, compare=False, default=None
        )
        api_id: Optional[str] = field(
            hash=False, repr=True, compare=False, default=None
        )
        api_hash: Optional[str] = field(
            hash=False, repr=True, compare=False, default=None
        )

    @dataclass
    class Log(DataClassJsonMixin):
        level: Optional[str] = field(hash=False, repr=True, compare=False, default=None)
        logfile: Optional[str] = field(
            hash=False, repr=True, compare=False, default="log/tmp.log"
        )

    @dataclass
    class Slave(DataClassJsonMixin):
        enable: Optional[bool] = field(
            hash=False, repr=True, compare=False, default=None
        )
        name: Optional[str] = field(hash=False, repr=True, compare=False, default=None)

    dev_mode: Optional[bool] = field(hash=False, repr=True, compare=False, default=None)
    bot: Bot = Bot
    log: Log = Log
    admin: int = 5440674042
    slave = Slave


def load(initial: bool = False):
    """
    讀取設定用的東西
    usage: bot.config.loads()
    types: config 自己找找
    """
    filename = 'env_config.yml'
    env_config = os.getenv('ENV_CONFIG', filename)
    if not os.path.isfile(env_config):
        logger.critical('找不到 env_config.yml')
        sys.exit(1)

    with open(env_config, mode='r', encoding='utf8') as f:
        try:
            loads = safe_load(f.read())
        except (YAMLError, MarkedYAMLError):
            logger.critical('解讀 env_config.yml 錯誤')
            raise
        # check if set dev mode true.
        if loads.get('dev_mode') and initial:
            logger.warning('Set to Development mode.')
        opts = Config.from_dict(loads)
        # os.environ['http_proxy'] = opts.proxy.http
        # os.environ['https_proxy'] = opts.proxy.https
        return opts


@lru_cache
def get_config():
    return load(True)
