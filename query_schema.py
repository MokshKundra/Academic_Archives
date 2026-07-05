from pydantic import BaseModel, field_validator
from typing import Literal, Optional
import re
   
class NewChatRequest(BaseModel):
    course_id : str
    doc_type : Optional[Literal["slides", "pyqs", "notes", "textbook"]] = None
    title : Optional[str] = None
    rag_enable: bool = True

    @field_validator("course_id")
    @classmethod
    def sanitize(cls, v: str) -> str:
        v = v.strip().upper()
        v = re.sub(r"[^a-zA-Z0-9._-]", "_", v)
        v = re.sub(r"_+", "_", v)
        return v

    @field_validator("doc_type", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == "" else v
        
class ChatMessageRequest(BaseModel):
    question: str
    doc_type: str

    @field_validator("question")
    @classmethod
    def chk_empty(cls, v):
        if not v.strip():
            raise ValueError("question cannot be empty")
        return v