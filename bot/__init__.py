import asyncio
import logging
import sys
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from typing import Optional, Union

from pyrogram.client import Client
from pyrogram.errors import ApiIdInvalid, AuthKeyUnregistered
from pyrogram.session.session import Session
from pyrogram.types import User

from bot.config import Config, get_config
from bot.utils.http import HttpClient
from bot.utils.validators import get_tld

logger = logging.getLogger(__name__)


@dataclass
class Standby:
    ip: str
    asn: str
    region: str


@dataclass
class IpInfo:
    ip: str
    org: str
    region: str


class Bot(Client):
    _instance: Union[None, "Bot"] = None
    standby: Optional[Standby] = None
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
        info_str: str = (
            f'[Listening] {me.first_name} {me.last_name or ""}'
            f' (@{me.username or ""}) ID: {me.id}'
        )

        logger.info(info_str)
        self.me: User = me

    async def __get_standby(self):
        if not self.config.standby.enable:
            return None
        info: Optional[IpInfo] = None
        try:
            async with HttpClient() as s:
                r = await s.get('https://ipinfo.io')
                info = r.json()
        except JSONDecodeError:
            logger.error('ipinfo API Error')
            return None
        if info:
            ip = info['ip'].split('.')
            ip[-1] = '0'
            ip[-2] = '0'
            self.standby = Standby(
                ip='.'.join(e for e in ip), asn=info['org'], region=info['region']
            )
            logger.info(self.standby)

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
            await self.__get_standby()
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        await self.stop()

    def start_serve(self):
        loop: AbstractEventLoop = asyncio.get_event_loop()
        run = loop.run_until_complete
        run(self.__self_test())
        # fetch tld on start
        get_tld()

        logger.info('我就是速度~')

        self.run()
