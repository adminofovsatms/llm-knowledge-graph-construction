import json
import os
from agentic_pipeline.body_part_agent import BodyPartAgent
from agentic_pipeline.injury_agent import InjuryAgent

JSON_DIR = "llm-knowledge-graph/data/course/json-outputs"

body_agent = BodyPartAgent()
injury_agent = InjuryAgent()

for file in os.listdir(JSON_DIR):
    if file.endswith(".json"):
        path = os.path.join(JSON_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            diagnosis = data.get("injury_info", {}).get("diagnosis", {})
            injury_date = data.get("injury_info", {}).get("injury_date", "")
            injury_id = f"INJURY-{injury_date}-{file}"

            # 🧠 Create BodyPart
            body_part_name = diagnosis.get("body_region")
            side = diagnosis.get("side", "Center")
            if body_part_name:
                body_agent.upsert(body_part_name, side)

            # 🧠 Create Injury
            injury_agent.upsert({
                "injury_id": injury_id,
                "injury_date": injury_date,
                "pain_level": data.get("injury_info", {}).get("pain_level", "Moderate"),
                "pain_description": data.get("therapist_note", {}).get("subjective", ""),
                "body_region": body_part_name
            })

print("✅ Stick-figure injury graph created.")