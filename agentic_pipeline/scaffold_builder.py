from agentic_pipeline.config import graph, PERSON_NAME, BODY_PART_POSITIONS
import uuid

def create_person():
    query = """
    MERGE (p:Person {name: $name})
    SET p.role = 'patient'
    RETURN p
    """
    graph.query(query, {"name": PERSON_NAME})


def create_body_parts():
    for name, (x, y) in BODY_PART_POSITIONS.items():
        body_part_id = f"BODYPART-Center-{name}"
        query = """
        MERGE (b:BodyPart {body_part_id: $id})
        SET b.name = $name, b.side = "Center", b.x = $x, b.y = $y
        WITH b
        MATCH (p:Person {name: $person})
        MERGE (p)-[:HAS_BODY_PART]->(b)
        RETURN b
        """
        graph.query(query, {
            "id": body_part_id,
            "name": name,
            "x": x,
            "y": y,
            "person": PERSON_NAME
        })


def create_placeholder_injuries():
    body_parts = graph.query("MATCH (b:BodyPart) RETURN b.name as name, b.body_part_id as id")

    for bp in body_parts:
        injury_id = f"INJURY-{uuid.uuid4()}"
        diagnosis_id = f"DIAG-{uuid.uuid4()}"
        doctor_id = f"DOCTOR-{uuid.uuid4()}"
        treatment_id = f"TREATMENT-{uuid.uuid4()}"
        note_id = f"NOTE-{uuid.uuid4()}"
        medication_id = f"MED-{uuid.uuid4()}"

        query = """
        // Injury Node
        CREATE (i:Injury {injury_id: $injury_id, pain_level: 'N/A', pain_description: 'placeholder'})
        
        // Diagnosis Node
        CREATE (d:Diagnosis {diagnosis_id: $diagnosis_id, name: 'Unknown', body_region: $bp_name})
        
        // Doctor
        CREATE (doc:Doctor {doctor_id: $doctor_id, name: 'Dr. Placeholder'})
        
        // Treatment
        CREATE (t:Treatment {treatment_id: $treatment_id, type: 'N/A'})
        
        // Medical Note
        CREATE (n:MedicalNote {note_id: $note_id, subjective: '', objective: '', assessment: '', plan: ''})
        
        // Medication
        CREATE (m:Medication {medication_id: $medication_id, name: 'Placeholder Pill'})

        // Relationships
        WITH i, d, doc, t, n, m
        MATCH (p:Person {name: $person}), (b:BodyPart {body_part_id: $bp_id})
        MERGE (p)-[:HAD_INJURY]->(i)
        MERGE (i)-[:LOCATED_IN]->(b)
        MERGE (i)-[:HAS_DIAGNOSIS]->(d)
        MERGE (p)-[:DIAGNOSED_WITH]->(d)
        MERGE (p)-[:TREATED_BY]->(doc)
        MERGE (i)-[:TREATED_WITH]->(t)
        MERGE (p)-[:RECEIVED_NOTE]->(n)
        MERGE (t)-[:USED_MEDICATION]->(m)
        RETURN i, d, doc, t, n, m
        """

        graph.query(query, {
            "injury_id": injury_id,
            "diagnosis_id": diagnosis_id,
            "doctor_id": doctor_id,
            "treatment_id": treatment_id,
            "note_id": note_id,
            "medication_id": medication_id,
            "bp_name": bp["name"],
            "bp_id": bp["id"],
            "person": PERSON_NAME
        })


if __name__ == "__main__":
    print("👤 Creating person...")
    create_person()
    print("🦿 Creating body parts...")
    create_body_parts()
    print("💥 Creating placeholder injuries & links...")
    create_placeholder_injuries()
    print("✅ Stick-figure scaffold graph created successfully!")