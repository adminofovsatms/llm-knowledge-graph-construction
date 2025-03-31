import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain.prompts import PromptTemplate

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv('OPENAI_API_KEY'), 
    temperature=0
)

graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Only include the generated Cypher statement in your response.

Always use case insensitive search when matching strings.

Schema:
{schema}

Examples:
# Find all documents that mention a specific technology
MATCH (d:Document)<-[:PART_OF]-(:Chunk)-[:HAS_ENTITY]->(t:Technology)
WHERE t.id =~ '(?i)Langchain'
RETURN d

# Count all chunks
MATCH (c:Chunk)
RETURN COUNT(c) AS numberOfChunks

# Find people mentioned
MATCH (c:Chunk)-[:HAS_ENTITY]->(p:Person)
RETURN DISTINCT p.id

The question is:
{question}"""

cypher_generation_prompt = PromptTemplate(
    template=CYPHER_GENERATION_TEMPLATE,
    input_variables=["schema", "question"],
)

cypher_chain = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    cypher_prompt=cypher_generation_prompt,
    verbose=True,
    enhanced_schema=True,
    allow_dangerous_requests=True
)

def run_cypher(q):
    return cypher_chain.invoke({"query": q})

while (q := input("> ")) != "exit":
    print(run_cypher(q))