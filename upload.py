import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from upload_schema import Document
import re
from chunking import chunk_content
from providers.emb import get_embedding_function

client = chromadb.PersistentClient(path= "./chroma_db")
ef = get_embedding_function()

def addToCousreCollection(doc : Document):
    collection = client.get_or_create_collection(
        name= doc.course_id,
        embedding_function= ef
    )

    to_add = chunk_content(doc)
    collection.add(ids=to_add['ids'], documents= to_add['chunks'], metadatas= to_add['metas'])
