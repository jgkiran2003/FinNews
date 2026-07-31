import os, time, requests
from typing import Any, Dict, Optional

class BaseAPI:
    def __init__(
        self, 
        base_url: str, 
        *, 
        api_key_env: Optional[str] = None, 
        api_key: Optional[str] = None,
        rate_limit_s: float = 0.25, 
        timeout_s: float = 15.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or (os.getenv(api_key_env) if api_key_env else None)
        if not self.api_key:
            raise ValueError("API key not set")
        self.rate_limit_s = rate_limit_s
        self.timeout_s = timeout_s
        self._last = 0.0
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": "new_api/0.1"})

    def _throttle(self):
        dt = time.time() - self._last
        if dt < self.rate_limit_s:
            time.sleep(self.rate_limit_s - dt)
        self._last = time.time()

    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._throttle()
        url = f"{self.base_url}/{path.lstrip('/')}"
        r = self.s.get(url, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()