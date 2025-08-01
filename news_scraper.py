import requests
from bs4 import BeautifulSoup

# The URL of the news page we want to scrape
SOURCES = [
    {
        'name': 'Reuters Technology',
        'url': 'https://www.reuters.com/technology/',
        'selector': {
            'tag': 'a',
            'attrs': {'data-testid': 'Link'}
        }
    },
    {
        'name': 'BBC Technology',
        'url': 'https://www.bbc.com/news/technology',
        'selector': {
            'tag': 'h2',
            'attrs': {} # BBC uses a simple h2 tag, no special attributes needed
        }
    }
]

def fetch_headlines(url, selector):
    """
    Fetches and parses the headlines from a given URL, using a specific selector.
    """
    print(f"Fetching headlines from: {url}")
    try:
        # Send a request to the website with a User-Agent header
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'lxml')
        # Use the specific tag and attributes from the selector dictionary
        headlines = soup.find_all(selector['tag'], attrs=selector['attrs'])
        
        if not headlines:
            print("Could not find headlines with the specified selector.")
            return []
            
        # Extract the text from each headline element
        headline_texts = [h.get_text().strip() for h in headlines if h.get_text().strip()]
        return headline_texts

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

def main():
    """Main function to run the scraper."""
    for source in SOURCES:
        headlines = fetch_headlines(source['url'], source['selector'])
        
        if headlines:
            print(f"\n--- Latest Headlines from {source['name']} ---")
            # Print the top 5 headlines for brevity
            for i, headline in enumerate(headlines[:5], 1):
                print(f"{i}. {headline}")
        print("\n" + "="*20)


if __name__ == "__main__":
    main()