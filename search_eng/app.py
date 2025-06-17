import os
import re
import json
from datetime import datetime, timezone
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from get_documents import get_documents

def get_assessment_from_openai(api_key, product_id):
    """
    Calls OpenAI for a detailed ESG score AND recommendations, then parses the response.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # ================================================================
    # PROMPT IS ALREADY UPDATED TO REQUEST A SCORE OUT OF 100
    # ================================================================
    content = (
        "You are an expert ESG (Environmental, Social, Governance) assessor. Analyze the product from the given URL "
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

    urls, titles, text_docs = get_documents(product_id, top_n = 2)
    urls_rec, titles_rec, text_docs_rec = get_documents(titles[0], top_n = 2, get_recommendations = True)
    document_url = f"https://www.amazon.com/dp/{product_id}"
    print(f"{"\n".join(text_docs)}")
    query = f"{"\n".join(text_docs)}\nSource titles: {"\n".join(titles)}\nRecommendation info: {"\n".join(text_docs_rec)}\nGiven the above text, assess the product."
#     query = """KEMOVE K98SE Mechanical Gaming Keyboard, 98 Keys LED Backlit Programmable, 96% Wired Computer Keyboard with Double Sound Dampening Foam, Pre-lubed Red Switch
# Brand: KEMOVE
# 4.2 out of 5 stars    144 ratings
# S$93.81S$93.81

# Secure transaction

# Returns Policy
# Brand\tKEMOVE
# Compatible devices\tPC
# Connectivity technology\tUSB-C
# Keyboard description\tMechanical
# Recommended product uses\tGaming
# Special features\tBacklit
# Colour\tRed
# Number of keys\t98
# Keyboard backlight colour support\tSingle Color
# Style\tModern

# About this item:
# - Compact 96% Layout: The K98SE mechanical keyboard features a 98-key design that maximizes space efficiency, preserving essential letters, numbers, and function keys. This enables users to conveniently execute tasks in various scenarios.
# - Superior Mechanical Keyboard Experience: The red switch offers quiet, swift typing without noticeable tactile bumps and clicks. Ideal for gamers who prefer a serene atmosphere and rapid key presses. Pre-lubed switches and stabilizers elevate key feel and performance.
# - Classic Blue Backlight: The K98SE LED backlit keyboard offers 15 lighting effects with adjustable brightness and speed. The side light strip design enhances the lighting experience, adding a touch of fashion to the keyboard. Note: The light colour cannot be changed.
# - Software Support: K98SE wired keyboard software offers diverse features for customizing and enhancing your keyboard experience. It supports up to five profiles, with each profile allowing distinct key mappings, macro settings, and backlight configurations to cater to your diverse needs. Presently, it only supports Windows.
# - Optimized for Efficiency and Comfort: The K98SE gaming keyboard features double-shot keycaps and a two-stage kickstand, ensuring a premium experience. With full-key anti-ghosting, it eliminates delays, enabling you to enjoy efficient and seamless gaming and typing experiences.
# - Compatibility and After-Sales Service: Compatible with Windows 11/10/8/7/XP and Mac OS. Vista and Linux are only suitable for typing and office use."""

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": content}, {"role": "user", "content": query}],
        "temperature": 0.3,
    }

    try:
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
        
        # --- PARSING LOGIC FOR DETAILED SCORES ---
        def parse_score(pattern, text, default=0):
            match = re.search(pattern, text, re.IGNORECASE)
            # Handle cases like "score/10" by splitting and taking the first number
            if match:
                score_str = match.group(1).split('/')[0].strip()
                return int(score_str)
            return default


        # Environmental
        ghg_emissions = parse_score(r"Greenhouse Gas Emissions:\s*([\d\.]+)", assessment_text)
        material_sustainability = parse_score(r"Material Sustainability:\s*([\d\.]+)", assessment_text)
        water_usage = parse_score(r"Water Usage:\s*([\d\.]+)", assessment_text)
        packaging_impact = parse_score(r"Packaging impact:\s*([\d\.]+)", assessment_text)
        end_of_life = parse_score(r"End of Life Disposal:\s*([\d\.]+)", assessment_text)

        # Social
        fair_labour_match = re.search(r"Fair Labour \(yes/no\):\s*(yes|no)", assessment_text, re.IGNORECASE)
        fair_labour = 10 if fair_labour_match and fair_labour_match.group(1).lower() == 'yes' else 1
        worker_safety = parse_score(r"Worker Safety:\s*([\d\.]+)", assessment_text)
        fair_trade = parse_score(r"Fair Trade:\s*([\d\.]+)", assessment_text)
        local_sourcing = parse_score(r"Local Sourcing:\s*([\d\.]+)", assessment_text)
        community_impact = parse_score(r"Community Impact:\s*([\d\.]+)", assessment_text)
        user_health = parse_score(r"User Health and Safety:\s*([\d\.]+)", assessment_text)

        # Governance
        affordability = parse_score(r"Affordability/Value:\s*([\d\.]+)", assessment_text)
        circular_economy = parse_score(r"Circular Economy Fit:\s*([\d\.]+)", assessment_text)
        local_economic_impact = parse_score(r"Local Economic Impact:\s*([\d\.]+)", assessment_text)
        supply_chain_resilience = parse_score(r"Supply Chain Resilience:\s*([\d\.]+)", assessment_text)
        innovation = parse_score(r"Innovation/R&D:\s*([\d\.]+)", assessment_text)
        
        # --- CALCULATE WEIGHTED SCORES (REBASED TO 100) ---
        environmental_score = (
            (ghg_emissions * 0.35) +
            (material_sustainability * 0.15) +
            (water_usage * 0.10) +
            (packaging_impact * 0.20) +
            (end_of_life * 0.20)
        ) * 10

        social_score = (
            (fair_labour * 0.10) +
            (worker_safety * 0.10) +
            (fair_trade * 0.20) +
            (local_sourcing * 0.20) +
            (community_impact * 0.20) +
            (user_health * 0.20)
        ) * 10
        
        governance_score = (
            (affordability * 0.20) +
            (circular_economy * 0.25) +
            (local_economic_impact * 0.30) +
            (supply_chain_resilience * 0.15) +
            (innovation * 0.10)
        ) * 10

        # --- PARSE RECOMMENDATIONS ---
        recommendations = []
        alt_match = re.search(r"ALT:\s*(\[.*?\])", assessment_text, re.DOTALL | re.IGNORECASE)
        if alt_match:
            try:
                reco_json_str = alt_match.group(1)
                recommendations = json.loads(reco_json_str)
                
                # ================================================================
                # NEW: Post-processing to ensure score is out of 100
                # ================================================================
                for reco in recommendations:
                    if 'product_score' in reco and isinstance(reco['product_score'], (int, float)) and reco['product_score'] <= 10:
                        reco['product_score'] *= 10

            except json.JSONDecodeError as e:
                print(f"Error decoding recommendations JSON: {e}")
                recommendations = []
        
        # --- BUILD THE FINAL JSON OBJECT ---
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


# --- Flask Server (No changes needed) ---
app = Flask(__name__)
CORS(app)


@app.route("/api/assess", methods=["POST", "OPTIONS"])
def handle_assessment_request():
    print("enter")
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    if request.method == "POST":
        data = request.get_json()
        product_id = data.get("upc")
        if not product_id:
            return jsonify({"error": "upc is missing"}), 400
        api_key = os.getenv("API_KEY")
        print(api_key)
        if not api_key:
            return jsonify({"error": "API_KEY is not set on the server"}), 500
        result = get_assessment_from_openai(api_key, product_id)
        return jsonify(result)


if __name__ == "__main__":
    app.run(port=5001, debug=True)