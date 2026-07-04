import re
from pydantic import BaseModel, field_validator
from typing import Literal

class Document(BaseModel):
    course_id: str
    doc_title: str
    doc_type: Literal["slides", "pyqs", "notes", "textbook"]
    content: str

    @field_validator("course_id")
    @classmethod
    def sanitize_course_id(cls, v: str) -> str:
        v = v.strip().upper()
        v = re.sub(r"[^a-zA-Z0-9._-]", "_", v)
        v = re.sub(r"_+", "_", v)
        if not (3 <= len(v) <= 512):
            raise ValueError("course_id must be between 3 and 512 characters after sanitization")
        return v

    @field_validator("doc_title")
    @classmethod
    def sanitize_doc_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("doc_title cannot be empty")
        return v

    @field_validator("content")
    @classmethod
    def chk_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v