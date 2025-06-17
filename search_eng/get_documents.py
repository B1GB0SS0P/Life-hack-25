import requests
from bs4 import BeautifulSoup
import json


def get_documents(product_id, top_n=1, get_recommendations=False):
    """
    Retrieves text content from the top search results of a SearxNG search query.

    Args:
        product_id (str): A product name or ID used in the search query.
        top_n (int, optional): Number of top search results to retrieve. Defaults to 1.
        get_recommendations (bool, optional): If True, modifies the query to search for environmentally 
                                              friendly alternatives. Defaults to False.

    Returns:
        tuple: A tuple of three lists:
            - documents (list): URLs of retrieved documents.
            - titles (list): Titles of the search results.
            - txt (list): Extracted visible text from each URL.
    """
    # Choose the search prefix based on context
    query_prefix = "environmentally friendly alternatives to the " if get_recommendations else "Amazon UPC "

    # Search query parameters
    params = {
        "q": query_prefix + str(product_id),
        "format": "json",
        "language": "en",
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    search_url = "http://localhost:8080/search"

    titles = []
    documents = []
    txt = []

    try:
        # Send POST request to SearxNG instance
        response = requests.post(search_url, data=params, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("application/json"):
                data = response.json()

                # Extract top N titles and URLs
                for result in data.get("results", [])[:top_n]:
                    titles.append(result.get("title", "N/A"))
                    documents.append(result.get("url", "N/A"))
            else:
                print("Expected JSON but received:")
                print(response.text[:500])
        else:
            print(f"Error: Received status code {response.status_code}")
            print("Response content:")
            print(response.text)

    except requests.exceptions.Timeout:
        print("The request timed out. The server might be slow or unresponsive.")
    except requests.exceptions.ConnectionError as e:
        print(f"A connection error occurred: {e}")
        print("Please ensure the SearxNG instance is running at http://127.0.0.1:8080/")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
        print("Response content (might not be valid JSON):")
        print(response.text)

    # Fetch and extract readable text from each URL
    for url in documents:
        try:
            page_response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(page_response.text, "html.parser")

            # Remove non-visible content
            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            # Extract and clean visible text
            text = soup.get_text(separator="\n", strip=True)
            txt.append(text)

        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve or parse content from {url}: {e}")
            txt.append("")

    return documents, titles, txt


if __name__ == "__main__":
    # Example usage (uncomment for testing)
    # docs, titles, texts = get_documents("042100005264", top_n=2)
    # print(docs)
    # print(titles)
    # print(texts[0][:1000])
    pass