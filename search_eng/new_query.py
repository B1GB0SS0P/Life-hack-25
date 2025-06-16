import os
import requests
import re # Import the regular expression module
from datetime import datetime, timezone

# This function simulates the core logic that would run on a server.
def get_mapped_scores_from_openai(upc: str):
    """
    Takes a UPC/ASIN, calls OpenAI, parses the result, and maps it to the desired JSON structure.
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set.")
        
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # NOTE: In a real application, you would scrape the URL for the text.
    # For this example, we are keeping the placeholder text.
    product_url = f"https://www.amazon.com/dp/{upc}"
    product_text = "SOL DE JANEIRO Rio Radiance Perfume Mist - solar floral fragrance with notes of tuberose, ylang ylang, and vanilla. Cruelty-free, vegan, paraben-free."

    content = (
        "You are an environmental impact assessor. "
        "Return evaluations using this exact format:\n\n"
        "1. Material of products: {score / 10}\n"
        "2. Transport of materials: {score / 10}\n"
        "3. Disposal methods of products: {score / 10}\n"
    )
    
    query = f"The url to the product is {product_url}\nThe contents of the site are: {product_text}\nAssess the product."

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": content}, {"role": "user", "content": query}],
        "temperature": 0.3,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # --- PARSING AND MAPPING LOGIC ---
        assessment_text = response.json()["choices"][0]["message"]["content"]
        
        # Use regular expressions to find scores like "X / 10"
        material_match = re.search(r"Material.*?:\s*(\d+)\s*/\s*10", assessment_text)
        transport_match = re.search(r"Transport.*?:\s*(\d+)\s*/\s*10", assessment_text)
        disposal_match = re.search(r"Disposal.*?:\s*(\d+)\s*/\s*10", assessment_text)

        # Extract score, convert to number, and scale to 100. Default to 0 if not found.
        material_score = int(material_match.group(1)) * 10 if material_match else 0
        transport_score = int(transport_match.group(1)) * 10 if transport_match else 0
        end_of_life_score = int(disposal_match.group(1)) * 10 if disposal_match else 0

        # Map the parsed scores to the JavaScript object structure
        mapped_output = {
            "upc": upc,
            # We map "Transport" score to "carbonScore" as it's a key carbon contributor
            "carbonScore": transport_score, 
            "materialScore": material_score,
            "endOfLifeScore": end_of_life_score,
            "source": 'openai-gpt-4o-mini',
            "fetchedAt": datetime.now(timezone.utc).isoformat()
        }
        return mapped_output

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return {"error": str(e)}

# --- Example of how to use the function ---
if __name__ == '__main__':
    # The Amazon product ID
    product_upc = "B0CW25XR5S" 
    scores = get_mapped_scores_from_openai(product_upc)
    print(scores)