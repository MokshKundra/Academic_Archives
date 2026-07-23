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
    total_chunks = len(to_add['chunks'])
    print(f"--- Embedding {total_chunks} chunks in batches ---")
    
    batch_size = 50
    for i in range(0, total_chunks, batch_size):
        batch_ids = to_add['ids'][i:i + batch_size]
        batch_chunks = to_add['chunks'][i:i + batch_size]
        batch_metas = to_add['metas'][i:i + batch_size]
        
        collection.add(
            ids=batch_ids, 
            documents=batch_chunks, 
            metadatas=batch_metas
        )
        
        print(f"Embedded batch {i//batch_size + 1}/{(total_chunks - 1)//batch_size + 1}")
