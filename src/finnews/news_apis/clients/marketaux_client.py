from typing import Any, Dict, Optional
from ..base import BaseAPI

class MarketAuxClient(BaseAPI):
    """
    Finance & Market News
    Docs: https://www.marketaux.com/documentation
    Env: MARKETAUX_API_KEY
    Free tier ~100 req/day — keep limits small and filter by recency.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            "https://api.marketaux.com/v1", 
            api_key_env="MARKETAUX_API_KEY", 
            api_key=api_key
        )

    def finance_market_news(
        self,
        *,
        symbols: Optional[str] = None,   # e.g. "AAPL,TSLA"
        search: Optional[str] = None,
        language: str = "en",
        countries: Optional[str] = None, # e.g. "us,gb,sg"
        limit: int = 25,
        page: int = 1,
        **extra: Any
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "api_token": self.api_key,
            "language": language,
            "limit": max(1, min(limit, 50)),
            "page": max(1, page),
        }
        if symbols: params["symbols"] = symbols
        if search: params["search"] = search
        if countries: params["countries"] = countries
        params.update(extra)  # allow published_after/before, industries, sources, sort, etc.
        return self._get("news/all", params=params)
