from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import Literal
import os
import re
import tempfile
from upload_schema import Document
from upload import addToCousreCollection
from pdf_upload import extractor
from retrival import augmente_and_generate
from query_schema import NewChatRequest, ChatMessageRequest
from chat_store import get_chat_meta, get_messages, append_message, list_chats, delete_chat, save_message_sources, toggle_rag
from chat_store import create_chat as store_create_chat
from chunking import chunk_content
from retrival import list_courses, list_docs_in_collection, delete_doc_from_collection, delete_collection
from job_store import list_jobs, get_job, create_job
from jobs import process_upload_job
import threading

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index_dual.html", encoding="utf-8") as f:
        return f.read()


def sanitize_course_id(v: str) -> str:
    v = v.strip().upper()
    v = re.sub(r"[^a-zA-Z0-9._-]", "_", v)
    v = re.sub(r"_+", "_", v)
    return v

@app.post("/add")
async def addToDatabase(file : UploadFile = File(...), course_id : str = Form(...), doc_title : str = Form(...), doc_type : Literal["slides", "pyqs", "notes", "textbook"] = Form(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name    

    sanitized_course_id = sanitize_course_id(course_id)

    job_id = create_job(
        course_id=sanitized_course_id,
        doc_title=doc_title,
        doc_type=doc_type
    )

    thread = threading.Thread(
        target=process_upload_job,
        args=(job_id, tmp_path, sanitized_course_id, doc_title, doc_type),
        daemon=True
    )
    thread.start()

    return {
        "status": "queued",
        "job_id": job_id,
        "course_id": sanitized_course_id,
        "doc_title": doc_title,
        "doc_type": doc_type
    }




@app.get("/chats")
def get_chats():
    return list_chats()

@app.post("/chats")
def create_chat(req : NewChatRequest):
    chat_id = store_create_chat(course_id= req.course_id, title= req.title, rag_enable= req.rag_enable)
    return get_chat_meta(chat_id)

@app.get("/chats/{chat_id}")
def get_chat(chat_id : str):
    meta = get_chat_meta(chat_id)
    messages = get_messages(chat_id)
    return {"meta" : meta, "messages" : messages}

@app.post("/chats/{chat_id}/message")
def send_message(chat_id: str, req: ChatMessageRequest):
    meta = get_chat_meta(chat_id)

    history = get_messages(chat_id)
    chat_hist = [
        {"role": m["role"], "content": m["content"]}
        for m in history[:-1]
    ]

    _, user_idx = append_message(chat_id, role="user", content=req.question)

    response, chunks = augmente_and_generate(
        question=req.question,
        doc_type= req.doc_type,
        course_id=meta["course_id"],
        chat_hist=chat_hist,
        chat_id= chat_id,
        rag_enable=meta["rag_enable"]
    )

    all_chunks = (
        chunks["pyq_chunks"] + chunks["slide_chunks"] +
        chunks["notes_chunks"] + chunks["tb_chunks"]
    )
    source_refs = [
        {
            "doc_title": c["source"],
            "page": c["page"],
            "doc_type": c["doc_type"],
            "relevance_score": c["score"]
        }
        for c in all_chunks
    ]

    _, assistant_idx = append_message(
        chat_id,
        role="assistant",
        content=response,
        source_refs=source_refs
    )

    save_message_sources(chat_id, assistant_idx, chunks)

    return {
        "answer": response,
        "source_refs": source_refs,
        "chat_id": chat_id,
        "message_idx": assistant_idx
    }

@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(chat_id: str):
    delete_chat(chat_id)
    return {"status": "deleted", "chat_id": chat_id}

@app.patch("/chats/{chat_id}/rag")
def toggle_rag_endpoint(chat_id: str):
    new_state = toggle_rag(chat_id)
    return {"chat_id": chat_id, "rag_enabled": new_state}


@app.post("/chats/{chat_id}/upload")
async def upload_in_chat( chat_id : str, file : UploadFile = File(...), doc_title : str = Form(...), doc_type : Literal["slides", "pyqs", "notes", "textbook"] = Form(...)) : 
    meta = get_chat_meta(chat_id)

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with tempfile.NamedTemporaryFile(delete= False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        extracted_content = extractor(tmp_path, doc_title)

        doc = Document(
            course_id=meta["course_id"],
            doc_title=doc_title,
            doc_type=doc_type,
            content=extracted_content
        )

        addToCousreCollection(doc)

        chunk_data = chunk_content(doc)
        formatted_chunks = [
            {
                "text": text,
                "source": doc.doc_title,
                "page": meta["page_number"],
                "doc_type": doc.doc_type,
                "score": 1.0   
            }
            for text, meta in zip(chunk_data['chunks'], chunk_data['metas'])
        ]

        _, msg_idx = append_message(
            chat_id,
            role="system",
            content=f"Uploaded **{doc.doc_title}** ({doc.doc_type}) — {len(formatted_chunks)} chunks uploaded to this chat."
        )

        save_message_sources(chat_id, msg_idx, formatted_chunks)

        return {
            "status": "success",
            "doc_title": doc.doc_title,
            "doc_type": doc.doc_type,
            "chunks_pinned": len(formatted_chunks)
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UPLOAD FAILED :: {str(e)}")
    finally:
        os.unlink(tmp_path)



@app.get("/courses")
def get_courses():
    return {"courses": list_courses()}

@app.get("/courses/{course_id}/documents")
def get_documents(course_id: str):
    try:
        documents = list_docs_in_collection(course_id.upper())
        return {"course_id": course_id.upper(), "documents": documents}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@app.delete("/courses/{course_id}/docs/{doc_title}")
def delete_document(course_id: str, doc_title: str):
    try:
        result = delete_doc_from_collection(course_id.upper(), doc_title)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@app.delete("/courses/{course_id}")
def delete_course(course_id: str):
    try:
        result = delete_collection(course_id.upper())
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    try:
        return get_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/jobs")
def all_jobs():
    return list_jobs()