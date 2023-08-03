import os
from unittest import mock


def mockenv(**envvars):
    return mock.patch.dict(os.environ, envvars)
