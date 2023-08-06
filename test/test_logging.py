from unittest import mock
from bot.utils.logging import configure
from bot.config import Config


@mock.patch('bot.utils.logging.Path')
@mock.patch('bot.utils.logging.logging')
@mock.patch('bot.utils.logging.coloredlogs')
@mock.patch('bot.utils.logging.get_config')
def test_configure(get_config, coloredlogs, logging, path):
    configure()
    get_config.assert_called_once_with()
    level = get_config.return_value.log.level
    filename = path.return_value
    log_config = {
        'version': 1,
        'root': {'handlers': ['file'], 'level': level},
        'loggers': {'bot': {}},
        'handlers': {
            'file': {
                'formatter': 'file',
                'class': 'logging.FileHandler',
                'level': level,
                'filename': filename.as_posix.return_value,
            },
        },
        'formatters': {
            'file': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            }
        },
    }
    logging.config.dictConfig.assert_called_once_with(log_config)
    coloredlogs.install.assert_called_once_with(level=level)


@mock.patch('bot.utils.logging.Path')
@mock.patch('bot.utils.logging.logging')
@mock.patch('bot.utils.logging.coloredlogs')
@mock.patch('bot.utils.logging.get_config')
def test_without_file_handler(get_config, coloredlogs, logging, path):
    get_config.return_value.log.logfile = ''
    configure()
    get_config.assert_called_once_with()
    level = get_config.return_value.log.level
    path.assert_not_called()
    log_config = {
        'version': 1,
        'root': {'handlers': [], 'level': level},
        'loggers': {'bot': {}},
        'handlers': {},
        'formatters': {},
    }
    logging.config.dictConfig.assert_called_once_with(log_config)
    coloredlogs.install.assert_called_once_with(level=level)


@mock.patch('bot.utils.logging.get_config')
def test_capability(get_config, caplog, tmp_path, default_logging_handlers):
    import logging

    logger = logging.getLogger()
    logfile = tmp_path / "tmp.log"
    get_config.return_value = Config(
        dev_mode=True,
        bot=Config.Bot(),
        log=Config.Log(None, logfile.as_posix()),
    )
    configure()
    # add default handlers for caplog and live logging
    for h in default_logging_handlers:
        logger.addHandler(h)
    logger = logging.getLogger()
    caplog.clear()
    logger.info("info-log-test")
    logger.warning("warn-log-test2")
    assert 'info-log-test' == caplog.records[0].msg
    assert 'warn-log-test2' == caplog.records[1].msg
    text = logfile.read_text()
    assert 'info-log-test' in text
    assert 'warn-log-test2' in text

    # check bot logger
    caplog.clear()
    logging.getLogger('bot').info("bot-log-test")
    assert 'bot-log-test' in caplog.messages
    logging.getLogger('bot.plugins.dig').info('bot-plugins-dig-test')
    assert 'bot-plugins-dig-test' in caplog.messages
