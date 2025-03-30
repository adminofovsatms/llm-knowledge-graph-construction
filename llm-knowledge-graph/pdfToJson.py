import pdfplumber
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
    with pdfplumber.open(file_path) as pdf:
        tables_data = []
        text_content = []
        
        for i, page in enumerate(pdf.pages):
            # Extract tables
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    tables_data.append(table)
            
            # Extract text
            text_content.append(f"--- PAGE {i+1} ---\n{page.extract_text()}")
        
        # Format tables as text with clear structure
        formatted_tables = []
        for i, table in enumerate(tables_data):
            table_text = [f"--- TABLE {i+1} ---"]
            for row in table:
                # Filter out None values and convert to strings
                row_cells = [str(cell) if cell is not None else "" for cell in row]
                table_text.append(" | ".join(row_cells))
            formatted_tables.append("\n".join(table_text))
        
        # Combine all content
        all_content = "\n\n".join(text_content)
        if formatted_tables:
            all_content += "\n\n--- EXTRACTED TABLES ---\n\n" + "\n\n".join(formatted_tables)
        
        return all_content

def build_prompt(pdf_text, filename):
    return f"""
You are an expert in medical information extraction.

Given the following PDF content, extract it into a valid **JSON object** using this exact schema:

{{
  "document_id": "{filename}",
  "metadata": {{
    "title": "",
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
  "player_activity": {{
    "category": "",
    "details": ""
  }},
  "venue": {{
    "location": "",
    "session": "",
    "period": ""
  }},
  "exhibit_25": [],
  "attached_files": {{
    "name": "",
    "size": "",
    "created_time": ""
  }}
}}

The PDF content contains tables and form fields with label-value pairs. Pay special attention to the table structure, where each row typically represents a field and its value. Use the labeled sections from the text to populate the corresponding fields in the JSON schema.

Now here is the raw PDF content with preserved table structure:

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
            try:
                extracted_json = extract_json_from_pdf(pdf_path)
                if extracted_json:
                    out_path = os.path.join(OUTPUT_DIR, file.replace(".pdf", ".json"))
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(extracted_json, f, indent=2)
                    print(f"✅ Saved JSON: {out_path}")
            except Exception as e:
                print(f"❌ Error processing {file}: {str(e)}")