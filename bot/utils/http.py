import ssl
from httpx import HTTPError, _api as http  # noqa: F401

from httpx import AsyncClient

# cache ssl context for perf
# See: https://github.com/encode/httpx/issues/838#issuecomment-1291224189
context = ssl.create_default_context()


class HttpClient(AsyncClient):
    def __init__(self, *, verify=context, **kw):
        if verify is not False:
            verify = verify or context
        super().__init__(verify=verify, **kw)
