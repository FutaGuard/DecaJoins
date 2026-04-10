import httpx


class HttpClient:
    """Async HTTP client context manager backed by httpx."""

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> httpx.AsyncClient:
        self._client = httpx.AsyncClient(**self._kwargs)
        return self._client

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.aclose()
