import logging
import os
from testing.utils import mockenv

import pytest

TEST_CONFIG = '''
dev_mode: true
'''

@pytest.fixture(scope="session")
def default_logging_handlers():
    return list(logging.getLogger().handlers)


@pytest.fixture(scope="session")
def mk_config(tmp_path_factory):
    tmp_config = []

    def _mk_config(content):
        env_config = tmp_path_factory.mktemp('temp') / 'env_config.yml'
        env_config.write_text(content)
        tmp_config.append(env_config)
        return mockenv(ENV_CONFIG=env_config.as_posix())

    yield _mk_config

    for f in tmp_config:
        f.unlink()


@pytest.fixture(scope='session', autouse=True)
def mock_env_config(mk_config):
    if os.getenv('ENV_CONFIG', '') == '':
        with mk_config(TEST_CONFIG):
            yield
    else:
        yield
