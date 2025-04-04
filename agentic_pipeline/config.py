import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

# Initialize Neo4j client
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Person name for central node
PERSON_NAME = "Jonathan"

# Stick-figure coordinates
BODY_PART_POSITIONS = {
    # Head & Face
    "Head": (0, 5),
    "Forehead": (0, 5.2),
    "Face": (0.2, 4.8),
    "Jaw": (-0.2, 4.7),
    "Neck": (0, 4.5),

    # Upper Body
    "Chest": (0, 4),
    "Upper Back": (-0.3, 3.8),
    "Lower Back": (0, 3.2),
    "Shoulder Left": (-1.2, 4.2),
    "Shoulder Right": (1.2, 4.2),

    # Arms
    "Left Arm": (-1.8, 3.8),
    "Right Arm": (1.8, 3.8),
    "Left Elbow": (-2.2, 3.5),
    "Right Elbow": (2.2, 3.5),
    "Left Wrist": (-2.5, 3.2),
    "Right Wrist": (2.5, 3.2),
    "Left Hand": (-2.7, 3),
    "Right Hand": (2.7, 3),

    # Core & Pelvis
    "Abdomen": (0, 3),
    "Pelvis": (0, 2.5),
    "Groin": (0.2, 2.3),
    "Hip Left": (-0.8, 2.3),
    "Hip Right": (0.8, 2.3),

    # Legs
    "Left Thigh": (-1, 2),
    "Right Thigh": (1, 2),
    "Left Knee": (-1, 1.2),
    "Right Knee": (1, 1.2),
    "Left Calf": (-1, 0.6),
    "Right Calf": (1, 0.6),
    "Left Ankle": (-1, 0.2),
    "Right Ankle": (1, 0.2),
    "Left Foot": (-1, -0.3),
    "Right Foot": (1, -0.3),
}