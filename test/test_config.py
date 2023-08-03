import pytest
from testing.utils import mockenv
from unittest import mock
from yaml.error import YAMLError


@mock.patch('bot.config.logger')
def test_config_file_not_exists(logger):
    from bot.config import load

    with mockenv(ENV_CONFIG=''), pytest.raises(SystemExit):
        load()
        logger.critical.assert_called_once_with('找不到 env_config.yml')


@mock.patch('bot.config.logger')
def test_invalid_yaml(logger, mk_config):
    from bot.config import load

    with mk_config('bot_token: "xxx'), pytest.raises(YAMLError):
        load()
        logger.critical.assert_called_once_with('解讀 env_config.yml 錯誤')


@mock.patch('bot.config.logger')
def test_iniial(logger, mk_config):
    from bot.config import load, Config

    with mk_config(
        '''
dev_mode: true
bot:
    bot_token: "xxx"
    api_id: "yyy"
    api_hash: "zzz"
log:
    level: "ERROR"
    logfile: "/tmp/dont-care.log"
    '''
    ):
        config = load(initial=True)
        expected = Config(
            dev_mode=True,
            bot=Config.Bot(bot_token='xxx', api_id='yyy', api_hash='zzz'),
            log=Config.Log(level='ERROR', logfile='/tmp/dont-care.log'),
        )
        assert config.to_dict() == expected.to_dict()
        logger.warning.assert_called_once_with('Set to Development mode.')
