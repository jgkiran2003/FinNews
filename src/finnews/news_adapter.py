import os
from dotenv import load_dotenv
from typing import Any, List, Dict, Optional
from newsapi import NewsApiClient

class NewsAPIClientAdapter:
    """
    Thin wrapper around newsapi-python that normalizes output to Article.
    Env: NEWSAPI_API_KEY
    """
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        key = api_key or os.getenv("NEWSAPI_API_KEY")
        if not key:
            raise ValueError("NEWSAPI_API_KEY not set")
        self._client = NewsApiClient(api_key=key)

    def top_headlines(
        self,
        *,
        categories: List[str],
        countries: List[str],
        language: str = "en",
        page_size: int = 100,
        dedupe_by_title: bool = True,
        normalize: bool = False
    ) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        out: List[Dict[str, Any]] = []

        for country in countries:
            for category in categories:
                data: Dict[str, Any] = self._client.get_top_headlines(
                    category=category,
                    language=language,
                    country=country,
                    page_size=page_size,
                )
                if data.get("status") != "ok":
                    continue

                for a in data.get("articles", []):
                    title = (a or {}).get("title") or ""
                    if dedupe_by_title and (not title or title in seen):
                        continue
                    seen.add(title)

                    out.append(self._normalize_article(a) if normalize else a)

        return out

    def search_everything(
        self,
        q: str,
        *,
        language: str = "en",
        from_iso: Optional[str] = None,
        to_iso: Optional[str] = None,
        page_size: int = 100,
        sort_by: str = "publishedAt",
        normalize: bool = False
    ) -> List[Dict[str, Any]]:
        data = self._client.get_everything(
            q=q,
            language=language,
            from_param=from_iso,
            to=to_iso,
            page_size=page_size,
            sort_by=sort_by,
        )
        articles = data.get("articles", []) or []
        if not normalize:
            return articles
        return [self._normalize_article(a) for a in articles]
    
    @staticmethod
    def _normalize_article(a: Dict[str, Any]) -> Dict[str, Any]:
        """
        Minimal common dict keys without a dataclass.
        Keeps names close to MarketAux fields where possible.
        """
        return {
            "title": a.get("title"),
            "url": a.get("url"),
            "published_at": a.get("publishedAt"),
            "source": (a.get("source") or {}).get("name"),
            "description": a.get("description"),
            # for parity with MarketAux; NewsAPI doesn't provide tickers
            "tickers": [],
            "language": a.get("language") or "en",
            # keep the original object too if you ever need extra fields
            "_raw": a,
        }