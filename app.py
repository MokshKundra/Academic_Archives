from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import Literal
import os
import tempfile
from upload_schema import Document
from upload import addToCousreCollection
from pdf_upload import extractor
from retrival import augmente_and_generate
from query_schema import NewChatRequest, ChatMessageRequest
from chat_store import get_chat_meta, get_messages, append_message, list_chats, delete_chat, save_message_sources, toggle_rag
from chat_store import create_chat as store_create_chat

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index_dual.html", encoding="utf-8") as f:
        return f.read()


@app.post("/add")
async def addToDatabase(file : UploadFile = File(...), course_id : str = Form(...), doc_title : str = Form(...), doc_type : Literal["slides", "pyqs", "notes", "textbook"] = Form(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name    
    try:
        extracted_contents = extractor(tmp_path)
        doc = Document(
            course_id=course_id,
            doc_title=doc_title,
            doc_type=doc_type,
            content=extracted_contents
        )

        addToCousreCollection(doc)

        return {
            "status": "success",
            "course_id": doc.course_id,
            "doc_title": doc.doc_title,
            "doc_type": doc.doc_type,
            "pages_extracted": extracted_contents.count("--- Page")
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail= e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EXTRACTION FAILED :: {str(e)}")
    finally:
        os.unlink(tmp_path)





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