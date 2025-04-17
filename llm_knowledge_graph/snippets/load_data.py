from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

DOCS_PATH = "llm_knowledge_graph/data/course/pdfs"

loader = DirectoryLoader(DOCS_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)

docs = loader.load()