import requests
import json

params = {
    "q": "zero shot object detection",  # query to search
    "format": "json",
    "language": "en",
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

url = "http://localhost:8080/search"

top_n = 3

try:
    documents = []
    # Make the POST request
    response = requests.post(
        url, data=params, headers=headers, timeout=10
    )  # Changed to requests.post() and 'data'
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
            if data.get("results"):
                for result in data["results"][:top_n]:
                    # print(f"Title: {result.get('title', 'N/A')}")
                    documents.append(result.get("url", "N/A"))
                    print(f"URL: {result.get('url', 'N/A')}")
                    # print(f"Content: {result.get('content', 'N/A')[:150]}...\n")
                    # print(f"Content length: {len(result.get('content', 'N/A').split())}\n")
            else:
                print("No results found in the JSON response.")
                print(json.dumps(data, indent=2))
        else:
            print("Non-JSON response received:")
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

from bs4 import BeautifulSoup

for doc in documents:

    # Step 3: Fetch the web page content
    page_response = requests.get(doc, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page_response.text, "html.parser")

    # Step 4: Extract visible text content
    # You can refine this by removing nav/footers, scripts, etc.
    for script in soup(["script", "style", "noscript"]):
        script.extract()

    text = soup.get_text(separator="\n", strip=True)

    print("\n--- Extracted Text ---\n")
    print(text[:3000])
