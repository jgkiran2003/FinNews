import os
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Initialize the News API client with API key
load_dotenv()
API_KEY = os.getenv("NEWSAPI_API_KEY")
if not API_KEY:
    raise ValueError("API_KEY is not set. Please get a key from newsapi.org")
newsapi = NewsApiClient(api_key=API_KEY)


def fetch_news(categories, countries):
    """
    Fetches the top headlines for a list of categories and countries,
    then combines and de-duplicates them.
    """
    all_articles = []
    seen_titles = set()

    for country in countries:
        print(f"\nFetching news for country: {country.upper()} ---")
        for category in categories:
            print(f"\n  Fetching '{category}' headlines...")
            try:
                top_headlines = newsapi.get_top_headlines(
                    # q='',
                    # sources='',
                    category=category,
                    language='en',
                    country=country
                )
                
                if top_headlines.get('status') == 'ok':
                    for article in top_headlines.get('articles', []):
                        # De-duplicate articles based on their title
                        if article['title'] not in seen_titles:
                            all_articles.append(article)
                            seen_titles.add(article['title'])
                else:
                    print(f"XXXXXXX Error from API: {top_headlines.get('message')}")

            except Exception as e:
                print(f"    An error occurred: {e}")

    return all_articles

def main():
    """Main function to run the news fetcher."""
    categories_to_fetch = ['business', 'technology']
    countries_to_fetch = ['us', 'gb', 'ca', 'au', 'in']
    
    articles = fetch_news(categories_to_fetch, countries_to_fetch)
    
    if articles:
        print("\n--- Combined Top Headlines ---")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']} (Source: {article['source']['name']})")

    return articles

if __name__ == "__main__":
    main()