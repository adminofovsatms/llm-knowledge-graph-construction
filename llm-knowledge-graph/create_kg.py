import os
import json
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument
from dotenv import load_dotenv

load_dotenv()

# === PATHS ===
JSON_DIR = "data/course/json-outputs"

# === OpenAI Models ===
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4o"
)

embedding_provider = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-ada-002"
)

# === Neo4j Connection ===
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

def process_graph_document(graph_doc, filename):
    """Post-process a graph document to ensure it adheres to our schema"""

        # Normalize all node types to valid casing
    ALLOWED_NODE_TYPES = {
        "person": "Person",
        "event": "Event",
        "injury": "Injury",
        "diagnosis": "Diagnosis",
        "medicalnote": "MedicalNote",
        "location": "Location",
        "document": "Document",
        "bodypart": "BodyPart"
    }

    for node in graph_doc.nodes:
        if node.type:
            normalized = node.type.lower()
            if normalized in ALLOWED_NODE_TYPES:
                node.type = ALLOWED_NODE_TYPES[normalized]
    
    # Ensure nodes have required properties
    for node in graph_doc.nodes:
        if node.type == "Event" and not node.properties.get("event_id"):
            node.properties["event_id"] = f"EVENT-{node.properties.get('event_date', 'unknown')}-{filename}"
        
        if node.type == "Injury" and not node.properties.get("injury_id"):
            node.properties["injury_id"] = f"INJURY-{node.properties.get('injury_date', 'unknown')}-{filename}"
        
        if node.type == "Diagnosis" and not node.properties.get("diagnosis_id"):
            node.properties["diagnosis_id"] = f"DIAG-{node.properties.get('name', 'unknown')}-{filename}"
        
        if node.type == "MedicalNote" and not node.properties.get("note_id"):
            node.properties["note_id"] = f"NOTE-{node.properties.get('date', 'unknown')}-{filename}"
        
        # Add properties for BodyPart node if it exists
        if node.type == "BodyPart" and not node.properties.get("body_part_id"):
            body_region = node.properties.get("name", "unknown")
            side = node.properties.get("side", "unknown")
            node.properties["body_part_id"] = f"BODYPART-{side}-{body_region}-{filename}"
    
    # Find nodes by type
    event_nodes = [n for n in graph_doc.nodes if n.type == "Event"]
    injury_nodes = [n for n in graph_doc.nodes if n.type == "Injury"]
    diagnosis_nodes = [n for n in graph_doc.nodes if n.type == "Diagnosis"]
    person_nodes = [n for n in graph_doc.nodes if n.type == "Person"]
    doc_nodes = [n for n in graph_doc.nodes if n.type == "Document"]
    med_note_nodes = [n for n in graph_doc.nodes if n.type == "MedicalNote"]
    location_nodes = [n for n in graph_doc.nodes if n.type == "Location"]
    
    # Create BodyPart node if it doesn't exist but we have diagnosis info
    body_part_nodes = [n for n in graph_doc.nodes if n.type == "BodyPart"]
    if not body_part_nodes and diagnosis_nodes:
        # Extract body region and side from diagnosis
        diagnosis = diagnosis_nodes[0]
        body_region = diagnosis.properties.get("body_region", "")
        side = diagnosis.properties.get("side", "")
        
        if body_region:
            body_part_node = Node(
                id=f"BODYPART-{side}-{body_region}-{filename}",
                type="BodyPart",
                properties={
                    "body_part_id": f"BODYPART-{side}-{body_region}-{filename}",
                    "name": body_region,
                    "side": side
                }
            )
            graph_doc.nodes.append(body_part_node)
            body_part_nodes = [body_part_node]
    
    # Get the player node (or just use the first person if no player role specified)
    player_nodes = [n for n in person_nodes if n.properties.get("role") == "player"]
    if not player_nodes and person_nodes:
        # Try to find a person who's likely the patient/player
        # This is a fallback if role isn't specified
        player_nodes = [person_nodes[0]]
    
    # Only proceed if we have a player/patient
    if player_nodes:
        player = player_nodes[0]
        
        # MAKE PERSON THE CENTER - CREATE DIRECT RELATIONSHIPS FROM PERSON TO ALL ENTITIES
        
        # 1. Person to Event: EXPERIENCED
        if event_nodes:
            # Remove any existing EXPERIENCED relationship
            graph_doc.relationships = [r for r in graph_doc.relationships 
                                    if not (r.source.type == "Person" and r.target.type == "Event" and r.type == "EXPERIENCED")]
            
            # Create direct relationship from person to event
            graph_doc.relationships.append(
                Relationship(
                    source=player,
                    target=event_nodes[0],
                    type="EXPERIENCED",
                    properties={"player_role": "affected"}
                )
            )
        
        # 2. Person to Injury: HAD_INJURY (new direct relationship)
        if injury_nodes:
            # Check if relationship already exists
            has_injury = any(
                r.source.type == "Person" and r.target.type == "Injury" and r.type == "HAD_INJURY"
                for r in graph_doc.relationships
            )
            
            if not has_injury:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=injury_nodes[0],
                        type="HAD_INJURY"
                    )
                )
        
        # 3. Person to Diagnosis: DIAGNOSED_WITH (new direct relationship)
        if diagnosis_nodes:
            # Check if relationship already exists
            diagnosed_with = any(
                r.source.type == "Person" and r.target.type == "Diagnosis" and r.type == "DIAGNOSED_WITH"
                for r in graph_doc.relationships
            )
            
            if not diagnosed_with:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=diagnosis_nodes[0],
                        type="DIAGNOSED_WITH"
                    )
                )
        
        # 4. Person to BodyPart: HAS_BODY_PART
        if body_part_nodes:
            # Check if relationship already exists
            has_body_part = any(
                r.source.type == "Person" and r.target.type == "BodyPart" and r.type == "HAS_BODY_PART"
                for r in graph_doc.relationships
            )
            
            if not has_body_part:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=body_part_nodes[0],
                        type="HAS_BODY_PART"
                    )
                )
        
        # 5. Person to MedicalNote: RECEIVED_NOTE (new direct relationship)
        if med_note_nodes:
            # Check if relationship already exists
            received_note = any(
                r.source.type == "Person" and r.target.type == "MedicalNote" and r.type == "RECEIVED_NOTE"
                for r in graph_doc.relationships
            )
            
            if not received_note:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=med_note_nodes[0],
                        type="RECEIVED_NOTE"
                    )
                )
        
        # 6. Person to Location: VISITED (new direct relationship)
        if location_nodes:
            # Check if relationship already exists
            visited = any(
                r.source.type == "Person" and r.target.type == "Location" and r.type == "VISITED"
                for r in graph_doc.relationships
            )
            
            if not visited:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=location_nodes[0],
                        type="VISITED"
                    )
                )
        
        # 7. Person to Document: DOCUMENTED_IN (new direct relationship)
        if doc_nodes:
            # Check if relationship already exists
            has_document = any(
                r.source.type == "Person" and r.target.type == "Document" and r.type == "DOCUMENTED_IN"
                for r in graph_doc.relationships
            )
            
            if not has_document:
                graph_doc.relationships.append(
                    Relationship(
                        source=player,
                        target=doc_nodes[0],
                        type="DOCUMENTED_IN"
                    )
                )
    
    # ALSO MAINTAIN OTHER KEY RELATIONSHIPS BETWEEN ENTITIES
    
    # Injury to BodyPart: LOCATED_IN
    if injury_nodes and body_part_nodes:
        located_in = any(
            r.source.type == "Injury" and r.target.type == "BodyPart" and r.type == "LOCATED_IN"
            for r in graph_doc.relationships
        )
        
        if not located_in:
            graph_doc.relationships.append(
                Relationship(
                    source=injury_nodes[0],
                    target=body_part_nodes[0],
                    type="LOCATED_IN"
                )
            )
    
    # Event to Injury: RESULTED_IN
    if event_nodes and injury_nodes:
        has_resulted_in = any(
            r.source.type == "Event" and r.target.type == "Injury" and r.type == "RESULTED_IN"
            for r in graph_doc.relationships
        )
        
        if not has_resulted_in:
            graph_doc.relationships.append(
                Relationship(source=event_nodes[0], target=injury_nodes[0], type="RESULTED_IN")
            )
    
    # Injury to Diagnosis: HAS_DIAGNOSIS
    if injury_nodes and diagnosis_nodes:
        has_diagnosis = any(
            r.source.type == "Injury" and r.target.type == "Diagnosis" and r.type == "HAS_DIAGNOSIS"
            for r in graph_doc.relationships
        )
        
        if not has_diagnosis:
            graph_doc.relationships.append(
                Relationship(source=injury_nodes[0], target=diagnosis_nodes[0], type="HAS_DIAGNOSIS")
            )
    
    return graph_doc


# === LLM Transformer Configuration ===
doc_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=[
        "Person", "Event", "Injury", "Diagnosis", "MedicalNote", 
        "Location", "Document", "BodyPart"
    ],
    allowed_relationships=[
        "EXPERIENCED", "RESULTED_IN", "HAS_DIAGNOSIS", "OCCURRED_AT", 
        "DOCUMENTED_IN", "ASSESSED_BY", "HAS_NOTE", "CREATED_BY", 
        "CREATED_FOR", "AUTHORED", "VERIFIED_BY", "HAS_BODY_PART", 
        "LOCATED_IN", "HAD_INJURY", "DIAGNOSED_WITH", "RECEIVED_NOTE", 
        "VISITED"  # Added new person-centric relationships
    ],
    node_properties=[
        # Person properties
        "name", "role",
        
        # Event properties
        "event_id", "event_type", "event_status", "event_date", "event_time", 
        "games_lost", "days_lost",
        
        # Injury properties
        "injury_id", "injury_date", "reported_date", "clearance_date", 
        "mechanism", "requires_surgery",
        
        # Diagnosis properties
        "diagnosis_id", "name", "side", "body_region", "icd9_code", "smdcs_code", 
        "verified_by_doctor", "is_reinjury",
        
        # MedicalNote properties
        "note_id", "date", "note_type", "subjective", "objective", 
        "assessment", "plan",
        
        # Location properties
        "venue_name", "session_type", "period",
        
        # Document properties
        "document_id", "title", "created_date",
        
        # BodyPart properties
        "body_part_id", "name", "side"
    ]
)

# Define our schema for LLM
schema_prompt = """
You are an expert in medical information extraction for a graph database.
When analyzing medical injury records, extract the following node types and relationships.
IMPORTANT: Make the Person node the central entity with direct relationships to all other entities.

Node Types:
1. Person - Players, therapists, doctors, and staff members
2. Event - The occurrence that resulted in an injury
3. Injury - Specific injury details including date, mechanism, etc.
4. Diagnosis - The medical diagnosis of the injury
5. MedicalNote - SOAP notes and assessments from medical staff
6. Location - Where the event occurred (venue, session type)
7. Document - The medical record document itself
8. BodyPart - The specific body part affected (e.g., "Hip / Groin")

Relationships FROM PERSON (these are the most important):
1. (Person)-[EXPERIENCED]->(Event) - A player experienced an event
2. (Person)-[HAD_INJURY]->(Injury) - A player had a specific injury
3. (Person)-[DIAGNOSED_WITH]->(Diagnosis) - A player was diagnosed with a condition
4. (Person)-[HAS_BODY_PART]->(BodyPart) - A person has the body part that was injured
5. (Person)-[RECEIVED_NOTE]->(MedicalNote) - A player received medical notes/assessment
6. (Person)-[VISITED]->(Location) - A player visited/was at a location
7. (Person)-[DOCUMENTED_IN]->(Document) - A player is documented in a record

Other important relationships:
1. (Event)-[RESULTED_IN]->(Injury) - An event resulted in an injury
2. (Injury)-[HAS_DIAGNOSIS]->(Diagnosis) - An injury has a specific diagnosis
3. (Injury)-[LOCATED_IN]->(BodyPart) - The injury is located in a specific body part
4. (Document)-[CREATED_BY]->(Person) - Who created the document
5. (Person)-[AUTHORED]->(MedicalNote) - Who authored medical notes

When extracting nodes and relationships from the text, be sure to:
1. Make the player/patient the central node with direct relationships to all other entities
2. Correctly identify people by their roles (player, therapist, doctor, staff)
3. Create a BodyPart node for each injured body part
4. Ensure the Person node has direct relationships to all other relevant nodes
"""

# Update the LLM with our schema
llm_with_schema = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4o"
)

# Provide schema context to the LLM
def get_schema_enhanced_llm():
    messages = [
        {"role": "system", "content": schema_prompt},
        {"role": "user", "content": "I'll be sending you medical injury records. Please extract the entities and relationships according to the schema, making sure the Person node is central with direct relationships to all other entities."}
    ]
    
    # Return initialized LLM
    return ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o"
    ).bind(messages=messages)

# Update transformer with schema-enhanced LLM
doc_transformer = LLMGraphTransformer(
    llm=get_schema_enhanced_llm(),
    allowed_nodes=[
        "Person", "Event", "Injury", "Diagnosis", "MedicalNote", 
        "Location", "Document", "BodyPart"
    ],
    allowed_relationships=[
        "EXPERIENCED", "RESULTED_IN", "HAS_DIAGNOSIS", "OCCURRED_AT", 
        "DOCUMENTED_IN", "ASSESSED_BY", "HAS_NOTE", "CREATED_BY", 
        "CREATED_FOR", "AUTHORED", "VERIFIED_BY", "HAS_BODY_PART", 
        "LOCATED_IN", "HAD_INJURY", "DIAGNOSED_WITH", "RECEIVED_NOTE", 
        "VISITED"  # Added new person-centric relationships
    ],
    node_properties=[
        # Person properties
        "name", "role",
        
        # Event properties
        "event_id", "event_type", "event_status", "event_date", "event_time", 
        "games_lost", "days_lost",
        
        # Injury properties
        "injury_id", "injury_date", "reported_date", "clearance_date", 
        "mechanism", "requires_surgery",
        
        # Diagnosis properties
        "diagnosis_id", "name", "side", "body_region", "icd9_code", "smdcs_code", 
        "verified_by_doctor", "is_reinjury",
        
        # MedicalNote properties
        "note_id", "date", "note_type", "subjective", "objective", 
        "assessment", "plan",
        
        # Location properties
        "venue_name", "session_type", "period",
        
        # Document properties
        "document_id", "title", "created_date", "created_by", "created_for",
        
        # BodyPart properties
        "body_part_id", "name", "side"
    ]
)

# === Create indices and constraints ===
schema_queries = [
    "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE (e.event_id) IS UNIQUE",
    "CREATE CONSTRAINT injury_id IF NOT EXISTS FOR (i:Injury) REQUIRE (i.injury_id) IS UNIQUE",
    "CREATE CONSTRAINT diagnosis_id IF NOT EXISTS FOR (d:Diagnosis) REQUIRE (d.diagnosis_id) IS UNIQUE",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
    "CREATE CONSTRAINT medical_note_id IF NOT EXISTS FOR (n:MedicalNote) REQUIRE n.note_id IS UNIQUE",
    "CREATE CONSTRAINT location_venue IF NOT EXISTS FOR (l:Location) REQUIRE (l.venue_name, l.session_type) IS UNIQUE",
    "CREATE CONSTRAINT bodypart_id IF NOT EXISTS FOR (b:BodyPart) REQUIRE b.body_part_id IS UNIQUE"
]

for query in schema_queries:
    try:
        graph.query(query)
    except Exception as e:
        print(f"Warning: Could not create constraint: {e}")

# === Load JSON files as LangChain Documents ===
docs = []

for file in os.listdir(JSON_DIR):
    if file.endswith(".json"):
        full_path = os.path.join(JSON_DIR, file)
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Add IDs to make node identification easier
            data["event_info"]["event_id"] = f"EVENT-{data.get('event_info', {}).get('event_date', '')}-{file}"
            data["injury_info"]["injury_id"] = f"INJURY-{data.get('injury_info', {}).get('injury_date', '')}-{file}"
            
            diagnosis = data.get("injury_info", {}).get("diagnosis", {})
            if diagnosis:
                diagnosis["diagnosis_id"] = f"DIAG-{diagnosis.get('name', '')}-{file}"
                
                # Create body part info
                body_region = diagnosis.get("body_region", "")
                side = diagnosis.get("side", "")
                if body_region:
                    # Add BodyPart node data to facilitate extraction
                    data["body_part"] = {
                        "body_part_id": f"BODYPART-{side}-{body_region}-{file}",
                        "name": body_region,
                        "side": side
                    }
            
            therapist_note = data.get("therapist_note", {})
            if therapist_note:
                therapist_note["note_id"] = f"NOTE-{therapist_note.get('date', '')}-{file}"
            
            # Fix document_id to use PDF name BEFORE dumping to JSON
            if data.get("document_id", "").endswith(".json"):
                data["document_id"] = file.replace(".json", ".pdf")

            document_id = data.get("document_id", file.replace(".json", ".pdf"))

            # Now convert to JSON string AFTER fixing document_id
            raw_text = json.dumps(data, indent=2)
            docs.append(Document(page_content=raw_text, metadata={"source": file, "document_id": document_id}))



print(f"📄 Loaded {len(docs)} JSON documents.")

# === Split into chunks ===
text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=10000,  # Larger chunk size to keep more context
    chunk_overlap=500,
)

chunks = text_splitter.split_documents(docs)

# === Process Each Chunk ===
for chunk in chunks:
    filename = chunk.metadata["source"]
    chunk_id = f"{filename}.chunk"

    print(f"🧠 Processing: {filename}")

    # === Create vector embedding
    chunk_embedding = embedding_provider.embed_query(chunk.page_content)

    # === Save document + chunk nodes to Neo4j
    properties = {
        "document_id": chunk.metadata["document_id"],
        "chunk_id": chunk_id,
        "text": chunk.page_content,
        "embedding": chunk_embedding
    }

    graph.query("""
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text
        WITH c
        CALL db.create.setNodeVectorProperty(c, 'textEmbedding', $embedding)
    """, properties)


    # === Extract nodes & relationships from chunk
    graph_docs = doc_transformer.convert_to_graph_documents([chunk])

    # === Connect extracted nodes to Chunk
    for graph_doc in graph_docs:
        chunk_node = Node(id=chunk_id, type="Chunk")
        for node in graph_doc.nodes:
            graph_doc.relationships.append(
                Relationship(source=chunk_node, target=node, type="HAS_ENTITY")
            )

        # Post-process to ensure our specific schema
        process_graph_document(graph_doc, filename)
        
        # Add to graph
        graph.add_graph_documents([graph_doc])

# === Create vector index (if not exists) ===
graph.query("""
    CREATE VECTOR INDEX `chunkVector`
    IF NOT EXISTS
    FOR (c: Chunk) ON (c.textEmbedding)
    OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }};
""")

# === Run additional queries to ensure Person-centric relationships ===
# Create any missing relationships to make Person the central node
graph.query("""
    // Find all players and related entities
    MATCH (p:Person {role: 'player'})
    OPTIONAL MATCH (i:Injury)
    OPTIONAL MATCH (d:Diagnosis)
    OPTIONAL MATCH (b:BodyPart)
    OPTIONAL MATCH (n:MedicalNote)
    OPTIONAL MATCH (l:Location)
    OPTIONAL MATCH (doc:Document)
    
    // Create direct relationships from person to all entities
    FOREACH(x IN CASE WHEN i IS NOT NULL AND NOT EXISTS((p)-[:HAD_INJURY]->(i)) THEN [1] ELSE [] END | 
      MERGE (p)-[:HAD_INJURY]->(i))
      
    FOREACH(x IN CASE WHEN d IS NOT NULL AND NOT EXISTS((p)-[:DIAGNOSED_WITH]->(d)) THEN [1] ELSE [] END | 
      MERGE (p)-[:DIAGNOSED_WITH]->(d))
      
    FOREACH(x IN CASE WHEN b IS NOT NULL AND NOT EXISTS((p)-[:HAS_BODY_PART]->(b)) THEN [1] ELSE [] END | 
      MERGE (p)-[:HAS_BODY_PART]->(b))
      
    FOREACH(x IN CASE WHEN n IS NOT NULL AND NOT EXISTS((p)-[:RECEIVED_NOTE]->(n)) THEN [1] ELSE [] END | 
      MERGE (p)-[:RECEIVED_NOTE]->(n))
      
    FOREACH(x IN CASE WHEN l IS NOT NULL AND NOT EXISTS((p)-[:VISITED]->(l)) THEN [1] ELSE [] END | 
      MERGE (p)-[:VISITED]->(l))
      
    FOREACH(x IN CASE WHEN doc IS NOT NULL AND NOT EXISTS((p)-[:DOCUMENTED_IN]->(doc)) THEN [1] ELSE [] END | 
      MERGE (p)-[:DOCUMENTED_IN]->(doc))
      
    RETURN p.name, count(i) as injuries, count(d) as diagnoses, count(b) as bodyParts, 
           count(n) as notes, count(l) as locations, count(doc) as documents
""")

print("✅ Knowledge graph with Person-centric relationships built successfully.")