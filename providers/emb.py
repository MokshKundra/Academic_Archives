from config import settings

def get_embedding_function():
    if settings.emb_provider == "ollama":
        return _emb_ollama()
    elif settings.emb_provider == "openai":
        return _emb_openai()
    elif settings.emb_provider == "huggingface":
        return _emb_huggingface()
    

def _emb_ollama():
    from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
    return OllamaEmbeddingFunction(
            model_name=settings.emb_model_ollama,
            url="http://localhost:11434"
        )

def _emb_openai():
    from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction
    return OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.emb_model_openai
    )

def _emb_huggingface():
    from chromadb.utils.embedding_functions.huggingface_embedding_function import HuggingFaceEmbeddingFunction
    return HuggingFaceEmbeddingFunction(
        api_key=settings.hf_api_key,
        model_name=settings.emb_model_huggingface 
    )