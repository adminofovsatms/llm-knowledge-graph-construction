import fitz  # PyMuPDF
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PDF_DIR = "data/course/health-pdf"
OUTPUT_DIR = "data/course/json-outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])

def build_prompt(pdf_text, filename):
    return f"""
You are an expert in medical information extraction.

Given the following PDF content, extract it into a valid **JSON object** using this exact schema:

{{
  "document_id": "{filename}",
  "metadata": {{
    "title": "Medial rotator strain",
    "player_name": "",
    "created_by": "",
    "created_for": "",
    "created_date": "",
    "event_time": {{
      "start": "",
      "end": ""
    }},
    "location": "",
    "period": ""
  }},
  "event_info": {{
    "event_type": "",
    "event_status": "",
    "games_lost": "",
    "event_date": "",
    "event-time": "",
    "days-lost": ""
  }},
  "injury_info": {{
    "injury_date": "",
    "reported_date": "",
    "clearance_date": null,
    "mechanism": "",
    "requires_surgery": false,
    "diagnosis": {{
      "name": "",
      "side": "",
      "body_region": "",
      "code": {{
        "ICD9": "",
        "SMDCS": ""
      }},
      "reinjury": ""
    }},
    "verified_by_doctor": true
  }},
  "therapist_note": {{
    "date": "",
    "author": "",
    "subjective": "",
    "objective": "",
    "assessment": "",
    "plan": ""
  }},
  "diagnosis_history": {{
    "created_by": "",
    "created_date": "",
    "event_name": null,
    "reinjury": "",
    "diagnosis_code": "",
    "smdcs_code": "",
    "description": "",
    "side": "",
    "body_region": ""
  }},
  "activity": {{
    "category": "",
    "details": ""
  }},
  "venue": {{
    "location": "",
    "session": "",
    "period": ""
  }},
  "exhibit_25": [],
  "raw_text_blocks": [
    {{
      "section": "Mechanism of Injury",
      "text": ""
    }},
    {{
      "section": "Diagnosis",
      "text": ""
    }},
    {{
      "section": "Therapist Note",
      "text": ""
    }}
  ]
}}

Now here is the raw PDF content:

\"\"\"{pdf_text}\"\"\"

Return only the JSON object. Do not include explanations or extra text.
"""

def extract_json_from_pdf(pdf_path):
    filename = os.path.basename(pdf_path)
    pdf_text = extract_text_from_pdf(pdf_path)
    prompt = build_prompt(pdf_text, filename)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    content = response.choices[0].message.content.strip()

    # Clean up markdown-style JSON wrappers if they exist
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()

    try:
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON for: {filename}")
        print("Raw content from GPT:\n", content)
        return None

if __name__ == "__main__":
    for file in os.listdir(PDF_DIR):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_DIR, file)
            print(f"📄 Processing: {file}")
            extracted_json = extract_json_from_pdf(pdf_path)
            if extracted_json:
                out_path = os.path.join(OUTPUT_DIR, file.replace(".pdf", ".json"))
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(extracted_json, f, indent=2)
                print(f"✅ Saved JSON: {out_path}")