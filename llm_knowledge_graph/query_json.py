import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0
)

JSON_DOCS_PATH = "data/course/json-outputs"

# Load all JSON files into a list
documents = []
for filename in os.listdir(JSON_DOCS_PATH):
    if filename.endswith(".json"):
        with open(os.path.join(JSON_DOCS_PATH, filename), "r") as f:
            try:
                documents.append(json.load(f))
            except json.JSONDecodeError as e:
                print(f"❌ Skipping {filename}: {str(e)}")

# Create a simple QA-style prompt
SYSTEM_PROMPT = """
You are a helpful assistant with access to structured JSON injury reports.
Use the provided context to answer the user's question precisely.
Only answer from the provided data. Do not hallucinate.
"""

USER_PROMPT = """
Question: {question}

Here are the reports:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_PROMPT)
])

def ask_question(question):
    full_context = json.dumps(documents, indent=2)
    chain = prompt | llm
    response = chain.invoke({"question": question, "context": full_context})
    return response.content

# CLI interface
if __name__ == "__main__":
    print("Ask a question about the JSON documents (type 'exit' to quit):")
    while (q := input("> ")) != "exit":
        print(ask_question(q))