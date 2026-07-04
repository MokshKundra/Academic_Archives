import json
import uuid
import os
from datetime import datetime 
from pathlib import Path

CHATS_DIR = Path("./chats")
CHATS_DIR.mkdir(exist_ok=True)

def create_chat(course_id : str, rag_enable : bool, title : str | None = None) -> str: 
    chat_id = str(uuid.uuid4())[:8]
    chat_dir = CHATS_DIR/chat_id
    chat_dir.mkdir()

    (chat_dir / "sources").mkdir(exist_ok=True)

    meta = {
        "chat_id" : chat_id,
        "course_id" : course_id ,
        "title" : title or f"Course:{course_id}::Chat {datetime.now().strftime('%b %d, %H:%M')}",
        "created_at" : datetime.now().isoformat(),
        "message_count" : 0,
        "rag_enable" : rag_enable
    }
    (chat_dir/"meta.json").write_text(json.dumps(meta, indent= 2))
    (chat_dir/"messages.json").write_text("[]")

    return chat_id

def get_chat_meta(chat_id : str) -> list[dict]:
    path = CHATS_DIR/chat_id/"meta.json"
    if not path.exists():
        raise ValueError(f"Chat {chat_id} not found")
    return json.loads(path.read_text())

def get_messages(chat_id : str) -> str:
    path = CHATS_DIR/chat_id/"messages.json"
    if not path.exists():
        raise ValueError(f"Chat {chat_id} not found")
    return json.loads(path.read_text())

def save_message_sources(chat_id : str, message_idx : int, chunks : dict):
    sources_dir = CHATS_DIR / chat_id / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    path = CHATS_DIR/chat_id/"sources"/f"msg_{message_idx}.json"
    path.write_text(json.dumps(chunks, indent=2))

def append_message(chat_id : str, role : str, content : str, source_refs : list[dict] = []) :
    messages = get_messages(chat_id)

    message = {
        "role" : role,
        "content" : content,
        "timestamp" : datetime.now().isoformat(),
        "source_refs" : source_refs
    }
    messages.append(message)
    msg_idx = len(messages) - 1

    chat_dir = CHATS_DIR/chat_id
    (chat_dir/"messages.json").write_text(json.dumps(messages, indent= 2))

    meta = get_chat_meta(chat_id)
    meta["message_count"] = len(messages)
    if role == "user" and meta["title"] == None and msg_idx == 0:
        meta["title"] = content[:50] + ("..." if len(content) > 50 else "")
    (chat_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    return message, msg_idx

def list_chats() -> list[dict]:
    chats = []
    for chat_dir in sorted(CHATS_DIR.iterdir(), reverse= True) : 
        meta_path = chat_dir/"meta.json"
        if meta_path.exists():
            chats.append(json.loads(meta_path.read_text()))
    return chats

def delete_chat(chat_id : str):
    import shutil
    chat_dir = CHATS_DIR/chat_id
    if not chat_dir.exists():
        raise ValueError(f"Chat {chat_id} not found")
    shutil.rmtree(chat_dir)

def toggle_rag(chat_id: str) -> bool:
    meta = get_chat_meta(chat_id)
    meta["rag_enable"] = not meta["rag_enable"]
    (CHATS_DIR / chat_id / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta["rag_enable"]