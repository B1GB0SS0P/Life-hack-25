import os
import re
import json
from datetime import datetime, timezone
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from get_documents import get_documents


def get_assessment_from_openai(api_key, product_id, custom_weights):
    """
    Calls OpenAI for a detailed ESG score AND recommendations, then parses the response.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    content = (
        "You are an expert ESG (Environmental, Social, Governance) assessor. Analyze the product from the given text "
        "and provide a detailed score breakdown. For each metric, provide a score from 1 (low) to 10 (high). "
        "For 'Fair Labour', answer with 'yes' or 'no'.\n"
        "RETURN YOUR EVALUATION USING THIS EXACT FORMAT:\n\n"
        "## Environmental Score ##\n"
        "- Greenhouse Gas Emissions: {score/10}\n"
        "- Material Sustainability: {score/10}\n"
        "- Water Usage: {score/10}\n"
        "- Packaging impact: {score/10}\n"
        "- End of Life Disposal: {score/10}\n\n"
        "## Social Score ##\n"
        "- Fair Labour (yes/no): {yes/no}\n"
        "- Worker Safety: {score/10}\n"
        "- Fair Trade: {score/10}\n"
        "- Local Sourcing: {score/10}\n"
        "- Community Impact: {score/10}\n"
        "- User Health and Safety: {score/10}\n\n"
        "## Governance Score ##\n"
        "- Affordability/Value: {score/10}\n"
        "- Circular Economy Fit: {score/10}\n"
        "- Local Economic Impact: {score/10}\n"
        "- Supply Chain Resilience: {score/10}\n"
        "- Innovation/R&D: {score/10}\n\n"
        "After the scores, list up to 3 sustainable alternative products as a JSON-compatible list of objects, starting with 'ALT:'. "
        "The product_score for these alternatives must be out of 100.\n"
        'Example: ALT: [{"product_name": "<item>", "product_score": 90, "reco_reason": "<reason>"}]'
    )

    # get documents from search engine
    urls, titles, text_docs = get_documents(product_id, top_n = 2)
    urls_rec, titles_rec, text_docs_rec = get_documents(titles[0], top_n = 2, get_recommendations = True)
    document_url = f"https://www.amazon.com/dp/{product_id}"
    print(f"{"\n".join(text_docs)}")
    query = f"{"\n".join(text_docs)}\nSource titles: {"\n".join(titles)}\nRecommendation info: {"\n".join(text_docs_rec)}\nGiven the above text, assess the product."

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": content}, {"role": "user", "content": query}],
        "temperature": 0.3,
    }

    try:
        # query llm given documents
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        assessment_text = response.json()["choices"][0]["message"]["content"]
        print(assessment_text, "CHECK THIS")

        if "do not have access" in assessment_text.lower() or "cannot access" in assessment_text.lower():
            return {
                "upc": product_id,
                "error": "AI model cannot access external websites to assess the product.",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "recommendations": [],
            }
        
        def parse_score(pattern, text, default=0):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score_str = match.group(1).split('/')[0].strip()
                return int(score_str)
            return default

        # Parsing logic for various components of esg standard reporting
        ghg_emissions = parse_score(r"Greenhouse Gas Emissions:\s*([\d\.]+)", assessment_text)
        material_sustainability = parse_score(r"Material Sustainability:\s*([\d\.]+)", assessment_text)
        water_usage = parse_score(r"Water Usage:\s*([\d\.]+)", assessment_text)
        packaging_impact = parse_score(r"Packaging impact:\s*([\d\.]+)", assessment_text)
        end_of_life = parse_score(r"End of Life Disposal:\s*([\d\.]+)", assessment_text)
        fair_labour_match = re.search(r"Fair Labour \(yes/no\):\s*(yes|no)", assessment_text, re.IGNORECASE)
        fair_labour = 10 if fair_labour_match and fair_labour_match.group(1).lower() == 'yes' else 1
        worker_safety = parse_score(r"Worker Safety:\s*([\d\.]+)", assessment_text)
        fair_trade = parse_score(r"Fair Trade:\s*([\d\.]+)", assessment_text)
        local_sourcing = parse_score(r"Local Sourcing:\s*([\d\.]+)", assessment_text)
        community_impact = parse_score(r"Community Impact:\s*([\d\.]+)", assessment_text)
        user_health = parse_score(r"User Health and Safety:\s*([\d\.]+)", assessment_text)
        affordability = parse_score(r"Affordability/Value:\s*([\d\.]+)", assessment_text)
        circular_economy = parse_score(r"Circular Economy Fit:\s*([\d\.]+)", assessment_text)
        local_economic_impact = parse_score(r"Local Economic Impact:\s*([\d\.]+)", assessment_text)
        supply_chain_resilience = parse_score(r"Supply Chain Resilience:\s*([\d\.]+)", assessment_text)
        innovation = parse_score(r"Innovation/R&D:\s*([\d\.]+)", assessment_text)
        
        # --- LOGIC TO USE CUSTOM OR DEFAULT WEIGHTS ---
        default_weights = {
            "environmental": {"ghg": 35, "material": 15, "water": 10, "packaging": 20, "eol": 20},
            "social": {"labour": 10, "safety": 10, "trade": 20, "sourcing": 20, "community": 20, "health": 20},
            "governance": {"affordability": 20, "circular": 25, "local": 30, "resilience": 15, "innovation": 10}
        }
        env_weights = custom_weights.get("environmental", default_weights["environmental"])
        soc_weights = custom_weights.get("social", default_weights["social"])
        gov_weights = custom_weights.get("governance", default_weights["governance"])

        # --- CALCULATIONS USE THE DYNAMIC WEIGHTS ---
        environmental_score = (
            (ghg_emissions * env_weights.get('ghg', 35) / 100) +
            (material_sustainability * env_weights.get('material', 15) / 100) +
            (water_usage * env_weights.get('water', 10) / 100) +
            (packaging_impact * env_weights.get('packaging', 20) / 100) +
            (end_of_life * env_weights.get('eol', 20) / 100)
        ) * 10

        social_score = (
            (fair_labour * soc_weights.get('labour', 10) / 100) +
            (worker_safety * soc_weights.get('safety', 10) / 100) +
            (fair_trade * soc_weights.get('trade', 20) / 100) +
            (local_sourcing * soc_weights.get('sourcing', 20) / 100) +
            (community_impact * soc_weights.get('community', 20) / 100) +
            (user_health * soc_weights.get('health', 20) / 100)
        ) * 10
        
        governance_score = (
            (affordability * gov_weights.get('affordability', 20) / 100) +
            (circular_economy * gov_weights.get('circular', 25) / 100) +
            (local_economic_impact * gov_weights.get('local', 30) / 100) +
            (supply_chain_resilience * gov_weights.get('resilience', 15) / 100) +
            (innovation * gov_weights.get('innovation', 10) / 100)
        ) * 10

        # --- Recommendation parsing ---
        recommendations = []
        alt_match = re.search(r"ALT:\s*(\[.*?\])", assessment_text, re.DOTALL | re.IGNORECASE)
        if alt_match:
            try:
                reco_json_str = alt_match.group(1)
                recommendations = json.loads(reco_json_str)
                for reco in recommendations:
                    if 'product_score' in reco and isinstance(reco['product_score'], (int, float)) and reco['product_score'] <= 10:
                        reco['product_score'] *= 10
            except json.JSONDecodeError as e:
                print(f"Error decoding recommendations JSON: {e}")
                recommendations = []
        
        # --- Build final JSON object ---
        formatted_data = {
            "upc": product_id,
            "environmentalScore": round(environmental_score),
            "socialScore": round(social_score),
            "governanceScore": round(governance_score),
            "source": "openai-gpt-4o-mini",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "recommendations": recommendations,
        }
        print("Formatted data:", json.dumps(formatted_data, indent=2))
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e), "recommendations": []}

# --- Flask Server ---
app = Flask(__name__)
CORS(app)

@app.route("/api/assess", methods=["POST", "OPTIONS"])
def handle_assessment_request():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Correctly extracts 'upc' and 'weights' from the request body
        product_id = data.get("upc")
        weights = data.get("weights", {}) 

        if not product_id:
            return jsonify({"error": "upc is missing"}), 400
        
        api_key = os.getenv("API_KEY")
        if not api_key:
            return jsonify({"error": "API_KEY is not set on the server"}), 500
        
        # Correctly passes 'weights' to the assessment function
        result = get_assessment_from_openai(api_key, product_id, weights)
        return jsonify(result)

if __name__ == "__main__":
    app.run(port=5001, debug=True)