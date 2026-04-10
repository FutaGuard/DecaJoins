import urllib.request
from functools import lru_cache
from pathlib import Path

_TLD_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
_TLD_CACHE = Path("/tmp/tlds.txt")


@lru_cache(maxsize=1)
def get_tld() -> frozenset[str]:
    """Fetch and cache the IANA TLD list."""
    if _TLD_CACHE.exists():
        raw = _TLD_CACHE.read_text(encoding="utf-8")
    else:
        try:
            with urllib.request.urlopen(_TLD_URL, timeout=5) as resp:
                raw = resp.read().decode("utf-8")
            _TLD_CACHE.write_text(raw, encoding="utf-8")
        except Exception:
            return frozenset()

    return frozenset(
        line.strip().lower()
        for line in raw.splitlines()
        if line.strip() and not line.startswith("#")
    )


def is_valid_domain(domain: str) -> bool:
    parts = domain.rstrip(".").split(".")
    if len(parts) < 2:
        return False
    tlds = get_tld()
    if not tlds:
        return True  # can't validate without list
    return parts[-1].lower() in tlds
