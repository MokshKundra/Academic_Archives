from pydantic_settings import BaseSettings
from typing import Literal, Optional


class Settings(BaseSettings):
    ext_provider : Literal["ollama", "openai", "gemini","groq", "huggingface", "zai"] = "ollama"
    ext_model_ollama: str = "doc-extractor"
    ext_model_openai: str = "gpt-4o" 
    ext_model_gemini: str = "gemini-3.1-flash-lite"
    ext_model_groq: str = "llama-3.3-70b-versatile"
    ext_model_huggingface: str = "llava-hf/llava-v1.6-mistral-7b-hf"
    ext_model_zai: str = "glm-4.6V-flash"


    emb_provider : Literal["ollama", "openai", "huggingface"] = "ollama"
    emb_model_ollama: str = "nomic-embed-text"
    emb_model_openai: str = "text-embedding-3-small"
    emb_model_huggingface: str = "sentence-transformers/all-MiniLM-L6-v2"

    gen_provider: Literal["ollama", "openai", "gemini","groq", "huggingface", "zai"] = "ollama"
    gen_model_ollama: str = "qwen3:8b"
    gen_model_openai: str = "gpt-4o"
    gen_model_gemini: str = "gemini-3.1-flash-lite"
    gen_model_groq: str = "llama-3.3-70b-versatile"
    gen_model_huggingface: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    gen_model_zai: str = "glm-4.7-flash"

    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None 
    hf_api_key: Optional[str] = None
    zai_api_key: Optional[str] = None

    model_config = {"env_file": ".env"}


settings = Settings()
