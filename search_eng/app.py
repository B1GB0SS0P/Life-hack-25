import os
import re
import json
from datetime import datetime, timezone
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS


def get_assessment_from_openai(api_key, product_id):
    """
    Calls OpenAI for scores AND recommendations, then parses the response.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # ================================================================
    # UPDATED PROMPT: Now asks for recommendations in a specific format
    # ================================================================
    content = (
        "You are an environmental impact assessor. Analyze the product from the given URL. "
        "First, return your evaluation using this exact format:\n"
        "1. Material of products: {score / 10}\n"
        "2. Transport of materials: {score / 10}\n"
        "3. Disposal methods of products: {score / 10}\n\n"
        "After the scores, on new lines, list up to 3 sustainable alternative products. "
        "THEY MUST BEGIN WITH THE WORD ALT:\n"
        "ALT: Reusable silicone food bags\n"
        "ALT: Glass containers with bamboo lids"
    )

    document_url = f"https://www.amazon.com/dp/{product_id}"
    query = f"Assess the product at the following URL: {document_url}"

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": content},
            {"role": "user", "content": query},
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        assessment_text = response.json()["choices"][0]["message"]["content"]
        print(assessment_text, "CHECK THIS")

        if (
            "do not have access" in assessment_text.lower()
            or "cannot access" in assessment_text.lower()
        ):
            return {
                "upc": product_id,
                "carbonScore": 0,
                "materialScore": 0,
                "endOfLifeScore": 0,
                "source": "openai-gpt-4o-mini",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "error": "AI model cannot access external websites to assess the product.",
                "recommendations": [],  # Include empty list in error case
            }
        # --- PARSING LOGIC FOR SCORES AND RECOMMENDATIONS ---
        material_match = re.search(
            r"Material.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE
        )
        transport_match = re.search(
            r"Transport.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE
        )
        disposal_match = re.search(
            r"Disposal.*?:\s*(\d+)\s*/\s*10", assessment_text, re.IGNORECASE
        )

        # ================================================================
        # NEW PARSING LOGIC: Extract recommendation lines
        # ================================================================
        recommendations = []
        print("Assessment text:", assessment_text)
        for line in assessment_text.splitlines():
            if line.strip().upper().startswith("ALT:"):
                # Clean up the line by removing the "ALT: " prefix
                recommendations.append(line.strip()[4:].strip())

        material_score = int(material_match.group(1)) * 10 if material_match else 0
        carbon_score = int(transport_match.group(1)) * 10 if transport_match else 0
        end_of_life_score = int(disposal_match.group(1)) * 10 if disposal_match else 0

        # --- BUILD THE FINAL JSON OBJECT (NOW WITH RECOMMENDATIONS) ---
        formatted_data = {
            "upc": product_id,
            "carbonScore": carbon_score,
            "materialScore": material_score,
            "endOfLifeScore": end_of_life_score,
            "source": "openai-gpt-4o-mini",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "recommendations": recommendations,  # Add the new list here
        }
        print("Formatted data:", json.dumps(formatted_data, indent=2))

        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e), "recommendations": []}


# --- Flask Server (No changes needed) ---
app = Flask(__name__)
CORS(app)


@app.route("/api/assess", methods=["POST", "OPTIONS"])
def handle_assessment_request():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    if request.method == "POST":
        data = request.get_json()
        product_id = data.get("upc")
        if not product_id:
            return jsonify({"error": "upc is missing"}), 400
        api_key = os.getenv("API_KEY")
        if not api_key:
            return jsonify({"error": "API_KEY is not set on the server"}), 500
        result = get_assessment_from_openai(api_key, product_id)
        return jsonify(result)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
