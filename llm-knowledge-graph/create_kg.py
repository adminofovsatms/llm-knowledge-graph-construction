import os
import json
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import Node, Relationship
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

# === Clear Existing Graph ===
print("🧹 Clearing existing graph...")
graph.query("MATCH (n) DETACH DELETE n")
print("✅ Graph cleared.")

# === LLM Transformer Configuration ===
doc_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=[
        "Person", "Injury", "BodyRegion", "Treatment", "Investigation",
        "Event", "Location", "MedicalProfessional", "TimePoint"
    ],
    allowed_relationships=[
        "SUFFERED", "LOCATED_IN", "WAS_TREATED_WITH", "WAS_INVESTIGATED_WITH",
        "WAS_ASSESSED_BY", "OCCURRED_AT", "HAS_TIMELINE", "LED_TO", "ADMINISTERED_BY"
    ],
    node_properties=[
        "name", "description", "date", "specialty", "severity",
        "type", "location", "result"
    ]
)

# === Load JSON files as LangChain Documents ===
docs = []

for file in os.listdir(JSON_DIR):
    if file.endswith(".json"):
        full_path = os.path.join(JSON_DIR, file)
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_text = json.dumps(data, indent=2)  # keep full structure
            docs.append(Document(page_content=raw_text, metadata={"source": file}))

print(f"📄 Loaded {len(docs)} JSON documents.")

# === Split into chunks ===
text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=1500,
    chunk_overlap=200,
)

chunks = text_splitter.split_documents(docs)

# === Process Each Chunk ===
for chunk in chunks:
    filename = chunk.metadata["source"]
    chunk_id = f"{filename}.0"

    print("🧠 Processing:", chunk_id)

    # === Create vector embedding
    chunk_embedding = embedding_provider.embed_query(chunk.page_content)

    # === Save document + chunk nodes to Neo4j
    properties = {
        "filename": filename,
        "chunk_id": chunk_id,
        "text": chunk.page_content,
        "embedding": chunk_embedding
    }

    graph.query("""
        MERGE (d:Document {id: $filename})
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text
        MERGE (d)<-[:PART_OF]-(c)
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

    graph.add_graph_documents(graph_docs)

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

print("✅ Knowledge graph built successfully.")