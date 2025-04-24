import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory, url_for
from flask_cors import CORS
from agentic_pipeline.config import graph, PERSON_NAME
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

JSON_DIR = "llm_knowledge_graph/data/course/json-outputs"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_matching_parts(body_region_text):
    """Use LLM to map body region descriptions to specific body parts."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a medical expert that maps body region descriptions to specific anatomical body parts.
                Return ONLY a valid JSON array of body parts that should be highlighted for the given injury.
                Example responses:
                - For "left knee": ["Left Knee"]
                - For "hip / groin": ["Hip Left", "Hip Right", "Groin"]
                - For "chest / ribs / upper back": ["Chest", "Upper Back"]
                
                Available body parts:
                Head, Neck, Chest, Abdomen, Pelvis, Shoulder Left, Shoulder Right, 
                Left Arm, Right Arm, Left Elbow, Right Elbow, Left Wrist, Right Wrist, 
                Left Hand, Right Hand, Hip Left, Hip Right, Left Thigh, Right Thigh, 
                Left Knee, Right Knee, Left Calf, Right Calf, Left Ankle, Right Ankle, 
                Left Foot, Right Foot, Upper Back, Lower Back, Groin.
                
                Return ONLY the JSON array, nothing else."""
            },
            {
                "role": "user",
                "content": f"Map this body region to specific body parts: '{body_region_text}'"
            }
        ],
        temperature=0.2
    )

    try:
        body = response.choices[0].message.content.strip()
        # Clean up any markdown or extra text
        if body.startswith("```json"):
            body = body.replace("```json", "").replace("```", "").strip()
        elif body.startswith("```"):
            body = body.replace("```", "").strip()
        
        # Ensure it's a valid JSON array
        parts = json.loads(body)
        if not isinstance(parts, list):
            print(f"❌ LLM returned non-list JSON for: {body_region_text}")
            return []
        return parts
    except Exception as e:
        print(f"❌ LLM mapping failed for: {body_region_text}\nError: {str(e)}\nResponse: {body}")
        # Fallback to simple mapping for common cases
        fallback_map = {
            "abdomen": ["Abdomen"],
            "hip / groin": ["Hip Left", "Hip Right", "Groin"],
            "chest / ribs / upper back": ["Chest", "Upper Back"],
            "wrist": ["Left Wrist", "Right Wrist"]
        }
        return fallback_map.get(body_region_text.lower(), [])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/timeline")
def get_timeline_years():
    years = []
    for file in os.listdir(JSON_DIR):
        if file.endswith(".json"):
            with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                injury_date = data.get("injury_info", {}).get("injury_date", "")
                try:
                    year = datetime.strptime(injury_date[:10], "%Y-%m-%d").year
                    if year not in years:
                        years.append(year)
                except:
                    continue
    return jsonify(sorted(years))

def get_json_by_year(year):
    for file in os.listdir(JSON_DIR):
        if file.endswith(".json"):
            with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                date_str = data.get("injury_info", {}).get("injury_date", "")
                try:
                    if datetime.strptime(date_str[:10], "%Y-%m-%d").year == int(year):
                        return data
                except:
                    continue
    return {}

def get_body_parts_with_injury_info(injured_parts, year, injury_details):
    query = """
    MATCH (p:Person {name: $name})-[:HAS_BODY_PART]->(b:BodyPart)
    RETURN b.name as name, b.x as x, b.y as y
    """
    parts = graph.query(query, {"name": PERSON_NAME})

    # Get the JSON data for the given year to extract body region
    data = get_json_by_year(year)
    raw_region = data.get("injury_info", {}).get("diagnosis", {}).get("body_region", "")
    
    # Use LLM to map the body region to specific body parts
    mapped_injured_parts = extract_matching_parts(raw_region)

    for p in parts:
        if p["name"] in mapped_injured_parts:
            p["color"] = "red"
            p["injury"] = injury_details
        else:
            p["color"] = "#bbb"
            p["injury"] = "No known injury for this body part."
    return parts

@app.route("/api/stick-figure")
def stick_figure():
    year = request.args.get("t")
    data = get_json_by_year(year)

    raw_region = data.get("injury_info", {}).get("diagnosis", {}).get("body_region", "")
    injured_parts = extract_matching_parts(raw_region)

    injury_details = data.get("therapist_note", {}).get("subjective", "No details available.")
    body_parts = get_body_parts_with_injury_info(injured_parts, year, injury_details)

    nodes, edges = [], []
    for bp in body_parts:
        nodes.append({
            "data": {
                "id": bp["name"],
                "label": bp["name"],
                "color": bp["color"],
                "injury": bp["injury"]
            },
            "position": {
                "x": bp["x"] * 100 + 400,
                "y": 600 - bp["y"] * 100
            }
        })

    connect = lambda a, b: edges.append({"data": {"id": f"{a}-{b}", "source": a, "target": b}})
    skeleton = [
        ("Head", "Neck"), ("Neck", "Chest"), ("Chest", "Abdomen"), ("Abdomen", "Pelvis"),
        ("Pelvis", "Left Thigh"), ("Pelvis", "Right Thigh"), ("Left Thigh", "Left Knee"),
        ("Right Thigh", "Right Knee"), ("Left Knee", "Left Calf"), ("Right Knee", "Right Calf"),
        ("Left Calf", "Left Ankle"), ("Right Calf", "Right Ankle"), ("Left Ankle", "Left Foot"),
        ("Right Ankle", "Right Foot"), ("Shoulder Left", "Left Arm"), ("Shoulder Right", "Right Arm"),
        ("Left Arm", "Left Elbow"), ("Right Arm", "Right Elbow"), ("Left Elbow", "Left Wrist"),
        ("Right Elbow", "Right Wrist"), ("Left Wrist", "Left Hand"), ("Right Wrist", "Right Hand"),
        ("Shoulder Left", "Chest"), ("Shoulder Right", "Chest"), ("Pelvis", "Hip Left"),
        ("Pelvis", "Hip Right")
    ]
    for a, b in skeleton:
        connect(a, b)

    return jsonify({"nodes": nodes, "edges": edges})

from llm_knowledge_graph.pdfToJson import extract_text_from_pdf

@app.route("/api/injury-story")
def get_injury_story():
    year = request.args.get("t")
    json_data = get_json_by_year(year)
    if not json_data:
        return jsonify({"error": "No data found for the given year."}), 404

    # Derive matching PDF filename from json["document_id"]
    document_id = json_data.get("document_id", "")
    pdf_file = document_id if document_id.endswith(".pdf") else document_id.replace(".json", ".pdf")
    pdf_path = os.path.join("llm_knowledge_graph", "data", "course", "health-pdf", pdf_file)

    if not os.path.exists(pdf_path):
        return jsonify({"error": "Related PDF not found."}), 404

    pdf_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are a helpful medical assistant.

Summarize the following medical report as a short, easy-to-understand injury story for doctors and patients.

Only highlight important details: when and where the injury happened, what body parts are involved, whether it needed surgery, how severe it was, and any next steps.

Here is the report content:

\"\"\"{pdf_text}\"\"\"

Provide the story in clear paragraphs. Avoid bullet points or technical jargon.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        summary = response.choices[0].message.content.strip()
        return jsonify({"story": summary})
    except Exception as e:
        return jsonify({"error": f"LLM Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)