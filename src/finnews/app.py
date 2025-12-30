from news_adapter import NewsAPIClientAdapter
import predict_text

# Prefer package import; fall back to relative when run as module
try:
    from storage import db as store
except Exception:
    from .storage import db as store  # type: ignore

def main_loop():
    try:
        # Initialize new storage
        store.init_db()
        # Optionally migrate legacy URLs once:
        # store.import_legacy_processed_urls()

        # Initialize adapter and fetch business news
        adapter = NewsAPIClientAdapter()
        articles = adapter.top_headlines(categories=['business'], countries=['us'], normalize=True)

        news_articles_found = 0
        for article in articles:
            url = article.get('url')
            if not url: continue
            title = article.get('title') or ''

            # Check existence before upsert
            existing_id = store.get_article_id_by_url(url)

            # Normalize fields
            provider = "newsapi"
            external_id = None
            published_at = article.get('published_at')
            source = article.get('source')
            language = article.get('language')
            tickers = article.get('tickers')

            article_id = store.upsert_article(
                provider=provider,
                external_id=external_id,
                url=url,
                title=title,
                published_at=published_at,
                source=source,
                language=language,
                tickers=tickers,
                raw_obj=article.get('_raw', article),
            )

            is_new = existing_id is None
            if is_new:
                news_articles_found += 1
                print(f"  -> New article added: {title} (URL: {url})")

            sentiment = predict_text.predict_sentiment(title)
            print(f"  -> Sentiment: {sentiment.upper()}")

            # Save sentiment if not already present
            if not store.has_sentiment(article_id):
                store.save_sentiment(article_id=article_id, engine="predict_text", score=None, label=sentiment)

            if sentiment in ['positive', 'negative']:
                print(f"  ALERT: {title} has a {sentiment} sentiment.")
        if news_articles_found == 0:
            print("No new articles found or all articles have been processed.")

    except Exception as e:
        print(f"An error occurred in the main loop: {e}")

if __name__ == "__main__":
    main_loop()
