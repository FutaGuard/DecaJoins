import os
import sys
from functools import lru_cache
from typing import Optional

import yaml
from loguru import logger
from pydantic import BaseModel


class BotConfig(BaseModel):
    bot_token: str
    api_id: int
    api_hash: str


class LogConfig(BaseModel):
    level: str = "DEBUG"
    logfile: Optional[str] = "log/tmp.log"


class StandbyConfig(BaseModel):
    enable: bool = False
    name: Optional[str] = None


class NodeHostConfig(BaseModel):
    """Config when running as the host/coordinator node."""

    bind: str = "0.0.0.0"
    port: int = 8080
    auth_token: str = "changeme"


class NodeConfig(BaseModel):
    """Multi-node mode configuration. mode can be: standalone or host."""

    mode: str = "standalone"  # 'standalone' or 'host'
    host: NodeHostConfig = NodeHostConfig()


class Config(BaseModel):
    dev_mode: bool = False
    bot: BotConfig
    log: LogConfig = LogConfig()
    standby: StandbyConfig = StandbyConfig()
    node: NodeConfig = NodeConfig()
    admin: int = 0


def load(initial: bool = False) -> Config:
    filename = "env_config.yml"
    env_config = os.getenv("ENV_CONFIG", filename)
    if not os.path.isfile(env_config):
        logger.critical("找不到 env_config.yml")
        sys.exit(1)

    with open(env_config, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data.get("dev_mode") and initial:
        logger.warning("Set to Development mode.")

    return Config(**data)


@lru_cache
def get_config() -> Config:
    return load(True)
