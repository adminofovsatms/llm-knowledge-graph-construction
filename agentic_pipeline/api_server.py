import os
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from agentic_pipeline.config import graph, PERSON_NAME
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

JSON_DIR = "llm-knowledge-graph/data/course/json-outputs"

# Simple normalization rules to map JSON values to graph node names
NORMALIZATION_RULES = {
    "hip / groin": ["Hip Left", "Hip Right", "Groin"],
    "chest / ribs / upper back": ["Chest", "Upper Back"]
}


def get_latest_json(timeline):
    def extract_date(json_data):
        date_str = json_data.get("injury_info", {}).get("injury_date", "")
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return datetime.min if timeline == "present" else datetime.max

    best_data, best_date = None, None
    for file in os.listdir(JSON_DIR):
        if file.endswith(".json"):
            with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                dt = extract_date(data)
                if best_date is None:
                    best_data, best_date = data, dt
                elif timeline == "present" and dt > best_date:
                    best_data, best_date = data, dt
                elif timeline == "past" and dt < best_date:
                    best_data, best_date = data, dt
    return best_data


def normalize_body_region(region):
    region = region.lower().strip()
    return NORMALIZATION_RULES.get(region, [])


def get_body_parts_with_injury_info(injured_parts, timeline, injury_details):
    query = """
    MATCH (p:Person {name: $name})-[:HAS_BODY_PART]->(b:BodyPart)
    RETURN b.name as name, b.x as x, b.y as y
    """
    parts = graph.query(query, {"name": PERSON_NAME})

    for p in parts:
        if p["name"] in injured_parts:
            p["color"] = "red" if timeline == "present" else "red"
            p["injury"] = injury_details
        else:
            p["color"] = "#bbb"
            p["injury"] = "No known injury for this body part."
    return parts


@app.route("/api/stick-figure")
def stick_figure():
    timeline = request.args.get("t", "past")
    json_data = get_latest_json(timeline)

    raw_region = json_data.get("injury_info", {}).get("diagnosis", {}).get("body_region", "")
    injured_parts = normalize_body_region(raw_region)

    injury_details = json_data.get("therapist_note", {}).get("subjective", "No details available.")
    body_parts = get_body_parts_with_injury_info(injured_parts, timeline, injury_details)

    nodes = []
    edges = []
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


if __name__ == "__main__":
    app.run(debug=True)