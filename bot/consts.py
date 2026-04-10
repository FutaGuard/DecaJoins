from pathlib import Path
from typing import FrozenSet

import yaml
from pydantic import BaseModel


class ConstsModel(BaseModel):
    bot_description: str
    supported_dns_types: list[str]


def _load_consts() -> ConstsModel:
    consts_path = Path(__file__).parent / "consts.yml"
    with open(consts_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ConstsModel(**data)


_consts = _load_consts()
BOT_DESCRIPTION: str = _consts.bot_description
SUPPORTED_DNS_TYPES: FrozenSet[str] = frozenset(_consts.supported_dns_types)
