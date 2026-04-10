import asyncio
import sys
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from json.decoder import JSONDecodeError
from typing import Optional, Union

import uvicorn
import validators
from loguru import logger
from pyrogram.client import Client
from pyrogram.errors import ApiIdInvalid, AuthKeyUnregistered
from pyrogram.session.session import Session
from pyrogram.types import User

from bot.config import Config, get_config
from bot.node.host import create_app
from bot.node.manager import manager
from bot.utils.http import HttpClient
from bot.utils.logging import configure
from bot.utils.validators import get_tld


@dataclass
class Standby:
    ip: str
    asn_org: str
    country: str


@dataclass
class IpConfig:
    ip: str
    asn_org: str
    country: str


class Bot(Client):
    _instance: Union[None, "Bot"] = None
    standby: Optional[Standby] = None
    config: Config

    def __init__(self):
        self.config = config = get_config()
        super().__init__(
            name="bot",
            api_id=config.bot.api_id,
            api_hash=config.bot.api_hash,
            bot_token=config.bot.bot_token,
            plugins=dict(root="bot/plugins"),
        )

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def __get_me(self) -> None:
        me: User = await self.get_me()
        logger.info(
            f"[Listening] {me.first_name} {me.last_name or ''}"
            f" (@{me.username or ''}) ID: {me.id}"
        )
        self.me = me  # type: ignore[override]

    async def __get_standby(self) -> None:
        if not self.config.standby.enable:
            return
        try:
            async with HttpClient() as s:
                r = await s.get("https://ipconfig.io/json", timeout=5)
                info_raw = r.json()
        except (JSONDecodeError, Exception) as e:
            logger.error(f"ipconfig.io API Error: {e}")
            return

        info = IpConfig(
            ip=info_raw["ip"],
            asn_org=info_raw["asn_org"],
            country=info_raw["country"],
        )
        if validators.ipv4(info.ip):
            parts = info.ip.split(".")
            parts[-1] = "0"
            parts[-2] = "0"
            masked = ".".join(parts)
        else:
            parts = info.ip.split(":")
            parts[-1] = "0000"
            parts[-2] = "0000"
            masked = ":".join(parts)

        self.standby = Standby(ip=masked, asn_org=info.asn_org, country=info.country)
        logger.info(f"Standby: {self.standby}")

    async def __self_test(self) -> None:
        # Suppress the pyrogram startup notice if the attribute exists
        try:
            Session.notice_displayed = True  # type: ignore[attr-defined]
        except AttributeError:
            pass
        try:
            await self.start()
        except (ApiIdInvalid, AttributeError):
            logger.critical("!!! API ID is invalid !!!")
            sys.exit(1)
        except AuthKeyUnregistered:
            logger.critical("!!! Session expired, removing and exiting !!!")
            await self.storage.delete()
            sys.exit(1)

        try:
            await self.__get_me()
        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        try:
            await self.__get_standby()
        except Exception as e:
            logger.exception(e)

        await self.stop()

    async def _run_host(self) -> None:
        """Run bot + FastAPI server together when node.mode == 'host'."""
        cfg = self.config.node.host
        uv_config = uvicorn.Config(
            create_app(),
            host=cfg.bind,
            port=cfg.port,
            log_level="warning",
        )
        server = uvicorn.Server(uv_config)
        manager.start()
        logger.info(f"Node hub listening on {cfg.bind}:{cfg.port}")
        try:
            await asyncio.gather(self.start(), server.serve())
        finally:
            manager.stop()

    def start_serve(self) -> None:
        configure(self.config.log.level)
        loop: AbstractEventLoop = asyncio.get_event_loop()
        loop.run_until_complete(self.__self_test())
        get_tld()
        logger.info("我就是速度~")

        if self.config.node.mode == "host":
            loop.run_until_complete(self._run_host())
        else:
            self.run()
