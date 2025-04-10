from flask import Flask, jsonify, request
from agentic_pipeline.config import graph, PERSON_NAME
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

def get_body_parts(timeline):
    query = """
    MATCH (p:Person {name: $name})-[:HAS_BODY_PART]->(b:BodyPart)
    OPTIONAL MATCH (i:Injury)-[:LOCATED_IN]->(b)
    WHERE $filter_date IS NULL OR date(i.injury_date) = date($filter_date)
    RETURN b.name as name, b.x as x, b.y as y,
           CASE WHEN i IS NOT NULL THEN
             CASE WHEN $timeline = 'past' THEN 'red' ELSE 'green' END
           ELSE '#bbb' END as color
    """
    filter_date = {
        "past": "2013-11-21",
        "present": "2018-09-20"
    }.get(timeline)
    return graph.query(query, {"name": PERSON_NAME, "filter_date": filter_date, "timeline": timeline})

@app.route("/api/stick-figure")
def stick_figure():
    timeline = request.args.get("t", "past")
    body_parts = get_body_parts(timeline)

    nodes = []
    edges = []

    for bp in body_parts:
        nodes.append({
            "data": {
                "id": bp["name"],
                "label": bp["name"],
                "color": bp["color"]
            },
            "position": {
                "x": bp["x"] * 100 + 400,
                "y": 600 - bp["y"] * 100
            }
        })

    connect = lambda a, b: edges.append({
        "data": {
            "id": f"{a}-{b}",
            "source": a,
            "target": b
        }
    })

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