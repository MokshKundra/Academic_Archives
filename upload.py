import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from upload_schema import Document
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from providers.emb import get_embedding_function

client = chromadb.PersistentClient(path= "./chroma_db")
ef = get_embedding_function()

def addToCousreCollection(doc : Document):
    collection = client.get_or_create_collection(
        name= doc.course_id,
        embedding_function= ef
    )

    parts = re.split(r"--- Page (\d+) ---", doc.content)

    pages = []
    for i in range(1, len(parts) - 1, 2):
        page_num = int(parts[i])
        page_text = parts[i + 1].strip()
        if page_text:
            pages.append((page_num, page_text))

    text_splitter = RecursiveCharacterTextSplitter()   
    
    
    all_ids, all_chunks, all_metadatas = [], [], []

    for page_num, page_text in pages:
        chunks = text_splitter.split_text(page_text)
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{doc.doc_title}_p{page_num}_chunk{i}")
            all_chunks.append(chunk)
            all_metadatas.append({
                "course_id": doc.course_id,
                "doc_title": doc.doc_title,
                "doc_type": doc.doc_type,
                "page_number": page_num,
                "chunk_idx": i
            })

    collection.add(ids=all_ids, documents=all_chunks, metadatas=all_metadatas)


    

    

