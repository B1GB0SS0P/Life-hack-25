import os
import re
import json
from datetime import datetime, timezone
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

def get_assessment_from_openai(api_key, product_id):
    """
    Calls the OpenAI API and handles both success and refusal responses.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    content = (
        "You are an environmental impact assessor. Analyze the product from the given URL. "
        "Strictly return your evaluation using this format and nothing else:\n\n"
        "1. Material of products: {score / 10}\n"
        "2. Transport of materials: {score / 10}\n"
        "3. Disposal methods of products: {score / 10}"
    )
    
    document_url = f"https://www.amazon.com/dp/{product_id}"
    query = f"Assess the product at the following URL: {document_url}"

    data = { "model": "gpt-4o-mini", "messages": [{"role": "system", "content": content}, {"role": "user", "content": query}], "temperature": 0.1 }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        assessment_text = response.json()["choices"][0]["message"]["content"]
        
        # ================================================================
        # THIS IS THE NEW LOGIC TO HANDLE THE AI'S REFUSAL
        # ================================================================
        if "do not have access" in assessment_text.lower() or "cannot access" in assessment_text.lower():
            print(f"OpenAI refused to access URL for {product_id}. Sending structured error.")
            return {
                "upc": product_id,
                "carbonScore": 0,
                "materialScore": 0,
                "endOfLifeScore": 0,
                "source": "openai-gpt-4o-mini",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "error": "AI model cannot access external websites to assess the product."
            }

        # --- PARSING LOGIC (from before) ---
        material_match = re.search(r"Material.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE)
        transport_match = re.search(r"Transport.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE)
        disposal_match = re.search(r"Disposal.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE)

        material_score = int(material_match.group(1)) * 10 if material_match else 0
        carbon_score = int(transport_match.group(1)) * 10 if transport_match else 0
        end_of_life_score = int(disposal_match.group(1)) * 10 if disposal_match else 0

        # --- BUILD THE FINAL JSON OBJECT ---
        formatted_data = {
            "upc": product_id,
            "carbonScore": carbon_score,
            "materialScore": material_score,
            "endOfLifeScore": end_of_life_score,
            "source": "openai-gpt-4o-mini",
            "fetchedAt": datetime.now(timezone.utc).isoformat()
        }
        print(formatted_data, "DFDKJSLFLDSF")
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

# --- Flask Server (No changes needed here) ---
app = Flask(__name__)
CORS(app)

@app.route('/api/assess', methods=['POST', 'OPTIONS'])
def handle_assessment_request():
    if request.method == 'OPTIONS': return jsonify({'status': 'ok'}), 200
    if request.method == 'POST':
        data = request.get_json()
        product_id = data.get('upc')
        if not product_id: return jsonify({"error": "upc is missing"}), 400
        api_key = os.getenv("API_KEY")
        if not api_key: return jsonify({"error": "API_KEY is not set on the server"}), 500
        result = get_assessment_from_openai(api_key, product_id)
        return jsonify(result)

if __name__ == '__main__':
    app.run(port=5001, debug=True)