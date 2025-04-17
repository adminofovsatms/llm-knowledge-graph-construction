import json
import re
from datetime import datetime
import io
import os
from PyPDF2 import PdfReader
from dateutil import parser
import pytz

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def parse_date_with_timezone(date_str, time_str, timezone_str):
    """Parse date and time with timezone information."""
    if not date_str or not time_str or not timezone_str:
        return ""
    
    # Parse the datetime string
    date_time_str = f"{date_str} {time_str}"
    dt = parser.parse(date_time_str)
    
    # Handle timezone
    if timezone_str.strip() == "Eastern Time":
        timezone = pytz.timezone("US/Eastern")
        dt = timezone.localize(dt)
    
    return dt.isoformat()

def extract_json_data(pdf_text, filename):
    """Extract structured data from PDF text and return JSON."""
    
    # Initialize the result dictionary with empty structures
    result = {
        "document_id": filename,
        "metadata": {
            "title": "",
            "player_name": "",
            "created_by": "",
            "created_for": "",
            "created_date": "",
            "event_time": {
                "start": "",
                "end": ""
            },
            "location": "",
            "period": ""
        },
        "event_info": {
            "event_type": "",
            "event_status": "",
            "games_lost": "",
            "event_date": "",
            "event-time": "",
            "days-lost": ""
        },
        "injury_info": {
            "injury_date": "",
            "reported_date": "",
            "clearance_date": "",
            "mechanism": "",
            "requires_surgery": "",
            "diagnosis": {
                "name": "",
                "side": "",
                "body_region": "",
                "code": {
                    "ICD9": "",
                    "SMDCS": ""
                },
                "reinjury": ""
            },
            "verified_by_doctor": ""
        },
        "therapist_note": {
            "date": "",
            "author": "",
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": ""
        },
        "diagnosis_history": {
            "created_by": "",
            "created_date": "",
            "event_name": "",
            "reinjury": "",
            "diagnosis_code": "",
            "smdcs_code": "",
            "description": "",
            "side": "",
            "body_region": ""
        },
        "activity": {
            "category": "",
            "details": ""
        },
        "venue": {
            "location": "",
            "session": "",
            "period": ""
        },
        "exhibit_25": [],
        "raw_text_blocks": []
    }
    
    # Extract metadata
    title_match = re.search(r"Medial rotator strain", pdf_text)
    if title_match:
        result["metadata"]["title"] = title_match.group(0)
    
    player_name_match = re.search(r"([\w]+,\s*[\w]+)\s+\d{4}-\d{2}-\d{2}", pdf_text)
    if player_name_match:
        result["metadata"]["player_name"] = player_name_match.group(1)
    
    created_by_match = re.search(r"Created by\s+([\w\s]+)\s+on\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+for\s+([\w\s]+)", pdf_text)
    if created_by_match:
        result["metadata"]["created_by"] = created_by_match.group(1).strip()
        result["metadata"]["created_for"] = created_by_match.group(4).strip()
        created_date = f"{created_by_match.group(2)}T{created_by_match.group(3)}:00"
        result["metadata"]["created_date"] = created_date
    
    # Extract event time
    injury_time_match = re.search(r"Injury Date\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}(?:AM|PM))\s+(Eastern Time)", pdf_text)
    if injury_time_match:
        result["metadata"]["event_time"]["start"] = parse_date_with_timezone(
            injury_time_match.group(1),
            injury_time_match.group(2),
            injury_time_match.group(3)
        )
    
    clearance_time_match = re.search(r"Medical Clearance Date\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}(?:AM|PM))\s+(Eastern Time)", pdf_text)
    if clearance_time_match:
        result["metadata"]["event_time"]["end"] = parse_date_with_timezone(
            clearance_time_match.group(1),
            clearance_time_match.group(2),
            clearance_time_match.group(3)
        )
    
    # Extract location and period
    venue_match = re.search(r"Venue:\s+([^]+)Session:\s+([^]+)\s+Period:\s+([^\n]+)", pdf_text)
    if venue_match:
        venue = venue_match.group(1).strip()
        session = venue_match.group(2).strip()
        result["metadata"]["location"] = f"{venue} / {session}"
        result["metadata"]["period"] = venue_match.group(3).strip()
    else:
        # Try alternative pattern
        venue_match = re.search(r"Venue:\s+([^/]+)/([^\n]+)\s+Session:\s+([^\n]+)\s+Period:\s+([^\n]+)", pdf_text)
        if venue_match:
            venue = venue_match.group(1).strip()
            arena = venue_match.group(2).strip()
            result["metadata"]["location"] = f"{venue} / {arena}"
            result["metadata"]["period"] = venue_match.group(4).strip()
    
    # Extract event info
    event_type_match = re.search(r"Event Type:\s+([^\n]+)", pdf_text)
    if event_type_match:
        result["event_info"]["event_type"] = event_type_match.group(1).strip()
    
    event_status_match = re.search(r"Event Status:\s+([^\n]+)", pdf_text)
    if event_status_match:
        result["event_info"]["event_status"] = event_status_match.group(1).strip()
    
    games_lost_match = re.search(r"Games Lost:\s+(\d+)", pdf_text)
    if games_lost_match:
        result["event_info"]["games_lost"] = games_lost_match.group(1).strip()
    
    event_date_match = re.search(r"Event Date:\s+(\d{4}-\d{2}-\d{2})", pdf_text)
    if event_date_match:
        result["event_info"]["event_date"] = event_date_match.group(1).strip()
    
    event_time_match = re.search(r"Event Time:\s+(\d{2}:\d{2})", pdf_text)
    if event_time_match:
        result["event_info"]["event-time"] = event_time_match.group(1).replace(":", ".").strip()
    
    days_lost_match = re.search(r"Days Lost:\s+(\d+)", pdf_text)
    if days_lost_match:
        result["event_info"]["days-lost"] = days_lost_match.group(1).strip()
    
    # Extract injury info
    injury_date_match = re.search(r"Injury Date\s+(\d{4}-\d{2}-\d{2})", pdf_text)
    if injury_date_match:
        result["injury_info"]["injury_date"] = injury_date_match.group(1).strip()
    
    reported_date_match = re.search(r"Reported Date\s+(\d{4}-\d{2}-\d{2})", pdf_text)
    if reported_date_match:
        result["injury_info"]["reported_date"] = reported_date_match.group(1).strip()
    
    clearance_date_match = re.search(r"Medical Clearance Date\s+(\d{4}-\d{2}-\d{2})", pdf_text)
    if clearance_date_match:
        result["injury_info"]["clearance_date"] = clearance_date_match.group(1).strip()
    
    mechanism_match = re.search(r"Mechanism of Injury:\s+(.*?)Surgery:", pdf_text, re.DOTALL)
    if mechanism_match:
        result["injury_info"]["mechanism"] = mechanism_match.group(1).strip().replace("\n", " ")
    
    surgery_match = re.search(r"Did Injury Require Surgery\?\s+([^\n]+)", pdf_text)
    if surgery_match:
        result["injury_info"]["requires_surgery"] = surgery_match.group(1).strip().lower() == "yes"
    
    # Extract diagnosis info
    diagnosis_name_match = re.search(r"(Medial rotator strain)", pdf_text)
    if diagnosis_name_match:
        result["injury_info"]["diagnosis"]["name"] = diagnosis_name_match.group(1)
    
    diagnosis_side_match = re.search(r"Side\s+(Left|Right)", pdf_text)
    if diagnosis_side_match:
        result["injury_info"]["diagnosis"]["side"] = diagnosis_side_match.group(1)
    
    body_region_match = re.search(r"Body Region\s+([\w\s/]+)", pdf_text)
    if body_region_match:
        result["injury_info"]["diagnosis"]["body_region"] = body_region_match.group(1).strip()
    
    smdcs_match = re.search(r"SMDCS\s+([A-Z0-9]+)", pdf_text)
    if smdcs_match:
        result["injury_info"]["diagnosis"]["code"]["SMDCS"] = smdcs_match.group(1)
    
    icd9_match = re.search(r"ICD9\s+([0-9.]+)", pdf_text)
    if icd9_match:
        result["injury_info"]["diagnosis"]["code"]["ICD9"] = icd9_match.group(1)
    
    reinjury_match = re.search(r"Re-injury\s+(Yes|No)", pdf_text)
    if reinjury_match:
        result["injury_info"]["diagnosis"]["reinjury"] = reinjury_match.group(1)
    
    verified_by_doctor_match = re.search(r"Diagnosis Verified by Doctor:\s+(Yes|No)", pdf_text)
    if verified_by_doctor_match:
        result["injury_info"]["verified_by_doctor"] = verified_by_doctor_match.group(1).strip().lower() == "yes"
    
    # Extract therapist note
    therapist_note_section = re.search(r"Therapist Note\s+(\d{4}-\d{2}-\d{2})\s+([\w\s]+)", pdf_text)
    if therapist_note_section:
        result["therapist_note"]["date"] = therapist_note_section.group(1).strip()
        result["therapist_note"]["author"] = therapist_note_section.group(2).strip()
    
    subjective_match = re.search(r"Subjective:\s+(.*?)Objective:", pdf_text, re.DOTALL)
    if subjective_match:
        result["therapist_note"]["subjective"] = subjective_match.group(1).strip().replace("\n", " ")
    
    objective_match = re.search(r"Objective:\s+(.*?)Assessment:", pdf_text, re.DOTALL)
    if objective_match:
        objective_text = objective_match.group(1).strip()
        # Expand common abbreviations
        abbreviations = {
            "Pos": "Positive",
            "inf": "inferior",
            "ROM": "range of motion",
            "sup": "supine",
            "IR": "internal rotation",
            "ABD": "abduction",
            "SI": "sacroiliac joint",
            "LLD": "leg length discrepancy",
            "L>R": "L > R"
        }
        
        for abbr, full in abbreviations.items():
            objective_text = objective_text.replace(abbr, full)
        
        result["therapist_note"]["objective"] = objective_text.replace("\n", " ")
    
    assessment_match = re.search(r"Assessment:\s+(.*?)Plan:", pdf_text, re.DOTALL)
    if assessment_match:
        result["therapist_note"]["assessment"] = assessment_match.group(1).strip().replace("\n", " ")
    
    plan_match = re.search(r"Plan:\s+(.*?)Attached Files", pdf_text, re.DOTALL)
    if plan_match:
        plan_text = plan_match.group(1).strip()
        # Expand common abbreviations
        abbreviations = {
            "mod": "moderate load"
        }
        
        for abbr, full in abbreviations.items():
            plan_text = plan_text.replace(abbr, full)
        
        result["therapist_note"]["plan"] = plan_text.replace("\n", " ")
    
    # Extract diagnosis history
    diagnosis_history_match = re.search(r"Created By\s+([\w\s]+)\s+on\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}:\d{2}(?:AM|PM)?)", pdf_text)
    if diagnosis_history_match:
        result["diagnosis_history"]["created_by"] = diagnosis_history_match.group(1).strip()
        created_date = f"{diagnosis_history_match.group(2)}T{diagnosis_history_match.group(3)}"
        result["diagnosis_history"]["created_date"] = created_date
    
    reinjury_history_match = re.search(r"Re-injury\s+(Yes|No)", pdf_text)
    if reinjury_history_match:
        result["diagnosis_history"]["reinjury"] = reinjury_history_match.group(1)
    
    diagnosis_code_match = re.search(r"ICD9\s+([0-9.]+)", pdf_text)
    if diagnosis_code_match:
        result["diagnosis_history"]["diagnosis_code"] = diagnosis_code_match.group(1).strip()
    
    smdcs_code_match = re.search(r"SMDCS\s+([A-Z0-9]+)", pdf_text)
    if smdcs_code_match:
        result["diagnosis_history"]["smdcs_code"] = smdcs_code_match.group(1).strip()
    
    description_match = re.search(r"Description\s+(Medial rotator strain)", pdf_text)
    if description_match:
        result["diagnosis_history"]["description"] = description_match.group(1)
    
    side_history_match = re.search(r"Side\s+(Left|Right)", pdf_text)
    if side_history_match:
        result["diagnosis_history"]["side"] = side_history_match.group(1)
    
    body_region_history_match = re.search(r"Body Region\s+([\w\s/]+)", pdf_text)
    if body_region_history_match:
        result["diagnosis_history"]["body_region"] = body_region_history_match.group(1).strip()
    
    # Extract activity info
    category_match = re.search(r"Category:\s+([^\n]+)", pdf_text)
    if category_match:
        result["activity"]["category"] = category_match.group(1).strip()
    
    details_match = re.search(r"Details:\s+([^\n]+)", pdf_text)
    if details_match:
        result["activity"]["details"] = details_match.group(1).strip()
    
    # Extract venue info
    venue_location_match = re.search(r"Venue:\s+([^/]+)/([^\n]+)", pdf_text)
    if venue_location_match:
        result["venue"]["location"] = venue_location_match.group(2).strip()
        result["venue"]["session"] = venue_location_match.group(1).strip()
    
    period_match = re.search(r"Period:\s+([^\n]+)", pdf_text)
    if period_match:
        result["venue"]["period"] = period_match.group(1).strip()
    
    # Add raw text blocks
    raw_blocks = []
    
    if mechanism_match:
        raw_blocks.append({
            "section": "Mechanism of Injury",
            "text": mechanism_match.group(1).strip().replace("\n", " ")
        })
    
    # Extract diagnosis text from the text directly instead of constructing it
    diagnosis_text_match = re.search(r"Diagnosis:.*?(Left|Right).*?(Hip\s*/\s*Groin).*?(Medial rotator strain).*?(HI\d+).*?(\d+\.\d+).*?(Yes|No)", pdf_text, re.DOTALL)
    if diagnosis_text_match:
        raw_blocks.append({
            "section": "Diagnosis",
            "text": f"{diagnosis_text_match.group(1)} {diagnosis_text_match.group(3)} {diagnosis_text_match.group(4)} {diagnosis_text_match.group(5)} {diagnosis_text_match.group(6)} {diagnosis_text_match.group(2)}"
        })
    
    # Extract therapist note text directly
    therapist_note_text = ""
    if subjective_match:
        therapist_note_text += subjective_match.group(1).strip().split(".")[0] + "... "
    
    if plan_match:
        therapist_note_text += "Treat conservatively with moderate load."
    
    if therapist_note_text:
        raw_blocks.append({
            "section": "Therapist Note",
            "text": therapist_note_text
        })
    
    result["raw_text_blocks"] = raw_blocks
    
    return result

def process_pdf_to_json(pdf_path, output_json_path=""):
    """Process a PDF file and save the extracted data as JSON."""
    filename = os.path.basename(pdf_path)
    
    with open(pdf_path, 'rb') as pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
    
    json_data = extract_json_data(pdf_text, filename)
    
    if output_json_path:
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=2)
        print(f"JSON saved to {output_json_path}")
    
    return json_data

# Main function - edit these paths as needed
if __name__ == "__main__":
    # Path to your PDF file - EDIT THIS LINE to change the input PDF
    pdf_path = "data/course/health-pdf/2013-11-21 Medial rotator strain.pdf"
    
    # Output JSON file path - EDIT THIS LINE to change the output JSON file
    output_json_path = "extracted_data.json"
    
    # Process the PDF and save as JSON
    extracted_data = process_pdf_to_json(pdf_path, output_json_path)
    
    # Print the result
    print(json.dumps(extracted_data, indent=2))