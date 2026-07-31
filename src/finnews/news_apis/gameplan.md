# Financial News APIs Summary

This document lists the APIs from [public-apis/public-apis](https://github.com/public-apis/public-apis) that are useful for the **Financial News Analysis App**.

---

## 📰 News Ingestion
| API | Link | Purpose |
|------|------|----------|
| **NewsAPI** | [https://newsapi.org/](https://newsapi.org/) | General news search and headlines filtering by date, source, and topic. |
| **GNews** | [https://gnews.io/](https://gnews.io/) | Google News–like API for global and multilingual coverage. |
| **Currents** | [https://currentsapi.services/](https://currentsapi.services/) | Real-time news across blogs and sources; useful for freshness. |
| **mediastack** | [https://mediastack.com/](https://mediastack.com/) | REST news API (by apilayer) for structured article data. |
| **MarketAux** | [https://www.marketaux.com/](https://www.marketaux.com/) | Finance-specific articles tagged with ticker symbols and sentiment. |

---

## 💹 Market Data
| API | Link | Purpose |
|------|------|----------|
| **Alpha Vantage** | [https://www.alphavantage.co/](https://www.alphavantage.co/) | Stock, FX, and crypto price data; good for tracking pre/post-news movement. |
| **Marketstack** | [https://marketstack.com/](https://marketstack.com/) | Real-time and historical market prices with easy endpoints. |
| **Alpaca Market Data** | [https://alpaca.markets/docs/api-references/market-data-api/](https://alpaca.markets/docs/api-references/market-data-api/) | Equities/ETF data with websocket support for live feeds. |

---

## 🧠 NLP & Sentiment Analysis
| API | Link | Purpose |
|------|------|----------|
| **Google Cloud Natural Language** | [https://cloud.google.com/natural-language](https://cloud.google.com/natural-language) | Entity extraction, sentiment analysis, and classification. |
| **IBM Watson Natural Language Understanding** | [https://www.ibm.com/watson/services/natural-language-understanding/](https://www.ibm.com/watson/services/natural-language-understanding/) | Detailed emotion, sentiment, and keyword analysis. |
| **MeaningCloud** | [https://www.meaningcloud.com/developer](https://www.meaningcloud.com/developer) | Text categorization and sentiment scoring for news text. |
| **Aylien News API** | [https://aylien.com/news-api/](https://aylien.com/news-api/) | Specialized NLP for finance and media monitoring. |

---

## 🌐 Enrichment & Utilities
| API | Link | Purpose |
|------|------|----------|
| **Clearbit Logo API** | [https://clearbit.com/logo](https://clearbit.com/logo) | Fetch company logos by domain for clean UI presentation. |
| **Fixer.io** | [https://fixer.io/](https://fixer.io/) | Currency exchange rates for financial normalization. |
| **Open Exchange Rates** | [https://openexchangerates.org/](https://openexchangerates.org/) | Alternative currency data API with good free tier. |

---

## ✅ Suggested Stack for Financial News Analysis App
| Function | API(s) |
|-----------|--------|
| **News ingestion** | NewsAPI + MarketAux |
| **Entity & sentiment extraction** | Google Cloud NL + MeaningCloud |
| **Market data integration** | Alpha Vantage |
| **UI enrichment** | Clearbit + Fixer |

---

**GitHub Source:** [https://github.com/public-apis/public-apis](https://github.com/public-apis/public-apis)

This list is curated for your app that collects **recent financial news**, performs **sentiment analysis**, and maps headlines to **market data movements**.
