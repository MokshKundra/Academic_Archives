from providers.gen import generate
import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from pathlib import Path
import json
from providers.emb import get_embedding_function

client = chromadb.PersistentClient(path= "./chroma_db")
ef = get_embedding_function()
   

def retrieve_from_db(question : str, course_id : str, doc_type: str = None) : 
    collection = client.get_collection(
        name= course_id,
        embedding_function= ef
    )

    where = None 
    if doc_type : 
        where = {"doc_type" : doc_type}

    results = collection.query(
        query_texts=[question],
        n_results= 10,
        where = where,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]) : 
        chunks.append({
            "text" : doc,
            "source" : meta["doc_title"],
            "page" : meta["page_number"],
            "doc_type" : meta["doc_type"],
            "score" : round(1 - dist, 3)
        })

    return chunks 

def retrieve_cross_reference(question: str, course_id: str) -> dict:
    pyq_chunks = retrieve_from_db(question, course_id, doc_type="pyqs")
    slide_chunks = retrieve_from_db(question, course_id, doc_type="slides")
    notes_chunks = retrieve_from_db(question, course_id, doc_type="notes")
    tb_chunks = retrieve_from_db(question, course_id, doc_type="textbook")
    
    return {
        "pyq_chunks": pyq_chunks,
        "slide_chunks": slide_chunks,
        "notes_chunks" : notes_chunks,
        "tb_chunks" : tb_chunks
    }

def build_context(pyq_chunks : list[dict], slide_chunks : list[dict], notes_chunks : list[dict], tb_chunks : list[dict]) -> str:
    pyq_part = "\n\n".join([
        f"PYQ - {c['source']}, page {c['page']} \n{c['text']}" for c in pyq_chunks
    ])

    slide_part = "\n\n".join([
        f"SLIDES - {c['source']}, page {c['page']} \n{c['text']}" for c in slide_chunks
    ])

    notes_part = "\n\n".join([
        f"NOTES - {c['source']}, page {c['page']} \n{c['text']}" for c in notes_chunks
    ])

    tb_part = "\n\n".join([
        f"TEXTBOOK - {c['source']}, page {c['page']} \n{c['text']}" for c in tb_chunks
    ])

    return f"""
            PAST YEAR QYESTION PAPER CONTENT: \n{pyq_part}
            SLIDES CONTENT: \n{slide_part}
            NOTES CONTENT: \n{notes_part}
            TEXTBOOK CONTENT: \n{tb_part}
            """

def augmente_and_generate(question : str, course_id : str, chat_id : str, rag_enable : bool, chat_hist : list[dict] = [], doc_type : str = None) : 
    if rag_enable:
        if doc_type:
            chunks = {
                "pyq_chunks": retrieve_from_db(question, course_id, doc_type=doc_type) if doc_type == "pyqs" else [],
                "slide_chunks": retrieve_from_db(question, course_id, doc_type=doc_type) if doc_type == "slides" else [],
                "notes_chunks": retrieve_from_db(question, course_id, doc_type=doc_type) if doc_type == "notes" else [],
                "tb_chunks": retrieve_from_db(question, course_id, doc_type=doc_type) if doc_type == "textbook" else []
            }
        else:
            chunks = retrieve_cross_reference(question, course_id)
    else:
        chunks = {"pyq_chunks": [], "slide_chunks": [], "notes_chunks": [], "tb_chunks": []}

    context = build_context(pyq_chunks=chunks['pyq_chunks'], slide_chunks=chunks['slide_chunks'], notes_chunks=chunks['notes_chunks'], tb_chunks=chunks['tb_chunks'])

    CHATS = Path("./chats")
    sources_path = CHATS / chat_id / "sources"
    
    previous_material_text = "None"
    if sources_path.exists():
        all_previous_chunks = []
        
        for msg_path in sources_path.iterdir():
            if msg_path.is_file():
                data = json.loads(msg_path.read_text())
                all_previous_chunks.extend(data.get("pyq_chunks", []))
                all_previous_chunks.extend(data.get("slide_chunks", []))
                all_previous_chunks.extend(data.get("notes_chunks", []))
                all_previous_chunks.extend(data.get("tb_chunks", []))

        unique_chunks = []
        seen = set()
        for chunk in all_previous_chunks:
            identifier = f"{chunk.get('source')}-{chunk.get('page')}"
            if identifier not in seen:
                seen.add(identifier)
                unique_chunks.append(chunk)

        max_chars = 15000
        current_chars = 0
        allowed_chunks = []
        
        for c in unique_chunks:
            chunk_text = f"Source: {c.get('source')}, Page: {c.get('page')}\n{c.get('text')}"
            if current_chars + len(chunk_text) > max_chars:
                break 
            allowed_chunks.append(chunk_text)
            current_chars += len(chunk_text)

        if allowed_chunks:
            previous_material_text = "\n\n".join(allowed_chunks)

    recent_chat_hist = chat_hist[-4:] if len(chat_hist) > 4 else chat_hist


    sys_prompt = f"""You are a helpful study assistant for {course_id}.
                    Answer the question detail in order to explain all the facts clearly.
                    Course material may be available so use that without fail if included.
                    The course material material will also be available from previoulsy pulled sources in the chat.
                    
                    PREVIOUSLY PULLED MATERIAL:
                    {previous_material_text}

                    COURSE MATERIAL: (maybe empty if RAG is turned off)
                    {context}"""
    
    messages = [{
        "role" : "system",
        "content" : sys_prompt
    }]
    messages += recent_chat_hist
    messages.append({
        "role" : "user",
        "content" : question
    })

    response = generate(messages=messages)

    return response, chunks