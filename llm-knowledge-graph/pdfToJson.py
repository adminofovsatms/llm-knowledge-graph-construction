import openai
import fitz  # PyMuPDF
import os
# Step 1: Read PDF content
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = "\n".join([page.get_text() for page in doc])
    return full_text

# Step 2: Prompt for OpenAI
def build_prompt(pdf_text):
    return f"""
You are an expert in information extraction.

Given the following PDF content, extract it into a **valid JSON object** using this strict schema:

{{
  "document_id": "2013-11-21 Medial rotator strain.pdf",
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

Return only the JSON object.
"""

# Step 3: Submit to OpenAI
def extract_json_from_pdf(pdf_path, api_key):
    pdf_text = extract_text_from_pdf(pdf_path)
    prompt = build_prompt(pdf_text)

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    return response['choices'][0]['message']['content']

# Example usage
if __name__ == "__main__":
    pdf_path = "data/course/health-pdf/2013-11-21 Medial rotator strain.pdf"
    api_key = os.getenv('OPENAI_API_KEY')  # take it from .env
    extracted_json = extract_json_from_pdf(pdf_path, api_key)
    print(extracted_json)
