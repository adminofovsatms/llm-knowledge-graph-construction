import matplotlib.pyplot as plt
from agentic_pipeline.config import graph, PERSON_NAME

def get_body_parts_with_coords():
    query = """
    MATCH (p:Person {name: $person})-[:HAS_BODY_PART]->(b:BodyPart)
    RETURN b.name as name, b.x as x, b.y as y
    """
    return graph.query(query, {"person": PERSON_NAME})

def get_injured_parts_by_month(year, month):
    cypher = """
    MATCH (p:Person {name: $person})-[:HAD_INJURY]->(i:Injury)
    WHERE date(i.injury_date).year = $year AND date(i.injury_date).month = $month
    MATCH (i)-[:LOCATED_IN]->(b:BodyPart)
    RETURN DISTINCT b.name AS name
    """
    return [row["name"] for row in graph.query(cypher, {"person": PERSON_NAME, "year": year, "month": month})]

def plot_stick_figure(year, month):
    body_parts = get_body_parts_with_coords()
    injured_parts = get_injured_parts_by_month(year, month)
    positions = {bp["name"]: (bp["x"], bp["y"]) for bp in body_parts}
    
    # Define skeletal connections
    edges = [
        ("Head", "Neck"),
        ("Neck", "Chest"),
        ("Chest", "Abdomen"),
        ("Abdomen", "Pelvis"),
        ("Pelvis", "Left Thigh"),
        ("Pelvis", "Right Thigh"),
        ("Left Thigh", "Left Knee"),
        ("Right Thigh", "Right Knee"),
        ("Left Knee", "Left Calf"),
        ("Right Knee", "Right Calf"),
        ("Left Calf", "Left Ankle"),
        ("Right Calf", "Right Ankle"),
        ("Left Ankle", "Left Foot"),
        ("Right Ankle", "Right Foot"),
        ("Shoulder Left", "Left Arm"),
        ("Shoulder Right", "Right Arm"),
        ("Left Arm", "Left Elbow"),
        ("Right Arm", "Right Elbow"),
        ("Left Elbow", "Left Wrist"),
        ("Right Elbow", "Right Wrist"),
        ("Left Wrist", "Left Hand"),
        ("Right Wrist", "Right Hand"),
        ("Shoulder Left", "Chest"),
        ("Shoulder Right", "Chest"),
        ("Pelvis", "Hip Left"),
        ("Pelvis", "Hip Right"),
        ("Face", "Head"),
        ("Forehead", "Head"),
        ("Jaw", "Head"),
    ]

    # Plot nodes
    for name, (x, y) in positions.items():
        color = "red" if name in injured_parts else "black"
        plt.scatter(x, y, color=color)
        plt.text(x, y + 0.05, name, fontsize=8, ha='center')

    for start, end in edges:
        if start in positions and end in positions:
            x_vals = [positions[start][0], positions[end][0]]
            y_vals = [positions[start][1], positions[end][1]]
            plt.plot(x_vals, y_vals, color="gray")

    plt.title(f"Stick Figure - Jonathan ({year}-{month:02})")
    plt.axis("off")
    plt.gca().invert_yaxis()
    plt.show()

if __name__ == "__main__":
    # Plot for past
    plot_stick_figure(2013, 11)

    # Plot for present
    plot_stick_figure(2018, 9)