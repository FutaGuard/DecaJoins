import logging
import logging.config
from pathlib import Path

import coloredlogs

from bot.config import get_config


def configure():
    config = get_config()
    level = config.log.level
    log_config = {
        'version': 1,
        'root': {
            'handlers': [],
            'level': level,
        },
        'loggers': {'bot': {}},
        'handlers': {},
        'formatters': {},
    }
    if config.log.logfile and config.log.logfile != '':
        try:
            filename = Path(config.log.logfile)
            if not filename.exists():
                basedir = (filename / '..').resolve()
                basedir.mkdir(parents=True, exist_ok=True)
                filename.touch()
        except (TypeError, OSError):
            raise
        log_config['handlers'].update(
            {
                'file': {
                    'formatter': 'file',
                    'class': 'logging.FileHandler',
                    'level': level,
                    'filename': filename.as_posix(),
                },
            }
        )
        log_config['formatters'].update(
            {
                'file': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                }
            }
        )
        log_config['root']['handlers'].append('file')

    logging.config.dictConfig(log_config)
    coloredlogs.install(level=level)
