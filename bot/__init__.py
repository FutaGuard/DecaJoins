import asyncio
import logging
import sys
from asyncio import AbstractEventLoop
from typing import Optional, Union

from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AuthKeyUnregistered
from pyrogram.session import Session
from pyrogram.types import User

from bot.config import Config, get_config
import httpx
from dataclasses import dataclass
from json.decoder import JSONDecodeError

logger = logging.getLogger(__name__)


@dataclass
class Slave:
    ip: str
    asn: str
    region: str


class Bot(Client):
    _instance: Union[None, "Bot"] = None
    slave: Optional[Slave] = None
    config: Config

    def __init__(self):
        self.config = config = get_config()
        super().__init__(
            name='bot',
            api_id=config.bot.api_id,
            api_hash=config.bot.api_hash,
            bot_token=config.bot.bot_token,
            plugins=dict(root='bot/plugins'),
        )

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def __get_me(self):
        me: User = await self.get_me()
        info_str: str = f'[Listening] {me.first_name}'
        info_str += f' {me.last_name}' if me.last_name else ''
        info_str += f' (@{me.username})' if me.username else ''
        info_str += f' ID: {me.id}'

        logger.info(info_str)
        self.me: User = me

    async def __get_slave(self):
        if not self.config.slave.enable:
            return None
        r = httpx.get('https://ipinfo.io')
        info: Optional[dict] = None
        try:
            info = r.json()
        except JSONDecodeError:
            logger.error('ipinfo API Error')
            return None
        else:
            ip = info['ip'].split('.')
            ip[-1] = '0'
            ip[-2] = '0'
            self.slave = Slave(
                ip='.'.join(e for e in ip),
                asn=info['org'],
                region=info['region']
            )
            logger.info(self.slave)

    async def __self_test(self):
        # Disable notice
        Session.notice_displayed = True
        try:
            await self.start()
        except (ApiIdInvalid, AttributeError):
            logger.critical('!!! API ID is invalid !!!')
            sys.exit(1)
        except AuthKeyUnregistered:
            logger.critical('!!! Session expired !!!')
            logger.critical("      Removing old session and exiting!")
            await self.storage.delete()
            exit(1)

        try:
            await self.__get_me()
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        try:
            await self.__get_slave()
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        await self.stop()

    def start_serve(self):
        loop: AbstractEventLoop = asyncio.get_event_loop()
        run = loop.run_until_complete
        run(self.__self_test())

        logger.info('我就是速度~')

        self.run()
