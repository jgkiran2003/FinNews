import news_api_fetcher
# import news_scraper
import predict_text
import database

def main_loop():
    try:
        articles = news_api_fetcher.main()

        news_articles_found = 0
        for article in articles:
            url = article['url']
            if not database.check_if_processed(url):    
                news_articles_found += 1
                print(f"  -> New article added: {article['title']} (URL: {url})")

                sentiment = predict_text.predict_sentiment(article['title'])
                print(f"  -> Sentiment: {sentiment.upper()}")

                if sentiment in ['positive', 'negative']:
                    print(f"  ALERT: {article['title']} has a {sentiment} sentiment.")
                
                database.add_processed_url(url)
        if news_articles_found == 0:
            print("No new articles found or all articles have been processed.")

    except Exception as e:
        print(f"An error occurred in the main loop: {e}")

if __name__ == "__main__":
    database.setup_database()
    main_loop()