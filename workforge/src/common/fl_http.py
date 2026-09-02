import httpx


def fl_get(url: str, **kwargs) -> httpx.Response:
    """GET to FL.ru without system proxy (trust_env=False)."""
    kwargs.setdefault("follow_redirects", True)
    with httpx.Client(trust_env=False) as client:
        return client.get(url, **kwargs)


def fl_request(method: str, url: str, **kwargs) -> httpx.Response:
    """HTTP request to FL.ru without system proxy (trust_env=False)."""
    kwargs.setdefault("follow_redirects", True)
    with httpx.Client(trust_env=False) as client:
        return client.request(method.upper(), url, **kwargs)
