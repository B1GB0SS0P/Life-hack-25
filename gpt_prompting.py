import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

params = {
    "q": "Amazon UPC B0CW25XR5S",  # query to search
    "format": "json",
    "language": "en",
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

url = "http://localhost:8080/search"

top_n = 1

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
                    print(f"Title: {result.get('title', 'N/A')}")
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

    # print("\n--- Extracted Text ---\n")
    # print(text[:3000])


api_key = os.getenv("API_KEY")  # Replace with your actual key

url = "https://api.openai.com/v1/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

content = (
    "You are an environmental impact assessor. "
    "Always return evaluations using this format:\n\n"
    "1. Material of products : {score / 10}\n"
    "2. Transport of materials to construction facilities: {score / 10}\n"
    "3. Disposal methods of products: {score / 10}\n"
    "Total Carbon Footprint Score: {score / 30}\n\n"
    "More sustainable alternative products:\n"
    "1) ...\n"
    "2) ..."
)


query = f"The url to the product is {documents[0]}\nThe contents of the site are as listed: {text}\n\
        Assess the product Amazon UPC B0CW25XR5S."

data = {
    "model": "gpt-4o-mini",  # Or "gpt-3.5-turbo"
    "messages": [{"role": "system", "content": content}, {"role": "user", "content": query}],
    "temperature": 0.7,
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(response.json()["choices"][0]["message"]["content"])
else:
    print("Error:", response.status_code, response.text)

# {
#   "id": "chatcmpl-abc123",
#   "object": "chat.completion",
#   "created": 1234567890,
#   "model": "gpt-4",
#   "choices": [
#     {
#       "index": 0,
#       "message": {
#         "role": "assistant",
#         "content": "The capital of France is Paris."
#       },
#       "finish_reason": "stop"
#     }
#   ],
#   "usage": {
#     "prompt_tokens": 12,
#     "completion_tokens": 7,
#     "total_tokens": 19
#   }
# }
