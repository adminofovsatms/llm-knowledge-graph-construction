import json
import os
from agentic_pipeline.body_part_agent import BodyPartAgent
from agentic_pipeline.injury_agent import InjuryAgent
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

JSON_DIR = "llm-knowledge-graph/data/course/json-outputs"

body_agent = BodyPartAgent()
injury_agent = InjuryAgent()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_matching_parts(body_region_text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that maps vague or combined body region descriptions to exact anatomical body parts in a stick figure diagram. Return only a JSON list of valid body parts from the following allowed parts: Head, Neck, Chest, Abdomen, Pelvis, Shoulder Left, Shoulder Right, Left Arm, Right Arm, Left Elbow, Right Elbow, Left Wrist, Right Wrist, Left Hand, Right Hand, Hip Left, Hip Right, Left Thigh, Right Thigh, Left Knee, Right Knee, Left Calf, Right Calf, Left Ankle, Right Ankle, Left Foot, Right Foot, Upper Back, Lower Back, Groin."
            },
            {
                "role": "user",
                "content": f"Given this body region description: '{body_region_text}', return only a JSON list of exact matching body parts."
            }
        ],
        temperature=0.2
    )

    try:
        body = response.choices[0].message.content.strip()
        return json.loads(body)
    except Exception as e:
        print(f"❌ LLM mapping failed for: {body_region_text}\n{e}")
        return []


for file in os.listdir(JSON_DIR):
    if file.endswith(".json"):
        path = os.path.join(JSON_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            diagnosis = data.get("injury_info", {}).get("diagnosis", {})
            injury_date = data.get("injury_info", {}).get("injury_date", "")
            injury_id = f"INJURY-{injury_date}-{file}"

            raw_region = diagnosis.get("body_region", "")
            side = diagnosis.get("side", "Center")

            mapped_parts = extract_matching_parts(raw_region)

            for part in mapped_parts:
                # 🧠 Create BodyPart node in graph
                body_agent.upsert(part, side)

                # 🧠 Create Injury node and connect to matched part
                injury_agent.upsert({
                    "injury_id": injury_id,
                    "injury_date": injury_date,
                    "pain_level": data.get("injury_info", {}).get("pain_level", "Moderate"),
                    "pain_description": data.get("therapist_note", {}).get("subjective", ""),
                    "body_region": part
                })

print("✅ Stick-figure injury graph created with LLM body mapping.")