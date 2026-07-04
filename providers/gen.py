from config import settings

def generate(messages : list[dict]) -> str:
    if settings.gen_provider == "ollama":
        return _gen_ollama(messages)
    elif settings.gen_provider == "openai":
        return _gen_openai(messages)
    elif settings.gen_provider == "gemini":
        return _gen_gemini(messages)
    elif settings.gen_provider == "groq":
        return _gen_groq(messages)
    elif settings.gen_provider == "huggingface":
        return _gen_huggingface(messages)
    

def _gen_ollama(messages : list[dict]) -> str:
    import ollama 
    response = ollama.chat(
        model = settings.gen_model_ollama,
        messages= messages
    )

    return response["message"]["content"]

def _gen_openai(messages : list[dict]) -> str:
    from openai import OpenAI
    client = OpenAI(api_key= settings.openai_api_key)

    response = client.chat.completions.create(
        model= settings.gen_model_openai,
        messages= messages
    )

    return response.choices[0].message.content


def _gen_gemini(messages: list[dict]) -> str:
    from google import genai
    
    client = genai.Client(api_key=settings.gemini_api_key)
    
    contents = []
    system_instruction = None
    
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        elif msg["role"] == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": msg["content"]}]
            })
        elif msg["role"] == "assistant":
            contents.append({
                "role": "model",
                "parts": [{"text": msg["content"]}]
            })
    
    config = None
    if system_instruction:
        config = genai.types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    
    response = client.models.generate_content(
        model=settings.gen_model_gemini,
        contents=contents,
        config=config
    )
    
    return response.text

def _gen_groq(messages : list[dict]) -> str:
    from groq import Groq
    client = Groq(api_key= settings.groq_api_key)

    response = client.chat.completions.create(
        model= settings.gen_model_groq,
        messages= messages
    )

    return response.choices[0].message.content

def _gen_huggingface(messages: list[dict]) -> str:
    from huggingface_hub import InferenceClient
    
    client = InferenceClient(api_key=settings.hf_api_key, model=settings.gen_model_huggingface)
    
    response = client.chat_completion(
        messages=messages,
        max_tokens=4096,
        temperature=0.7
    )
    
    return response.choices[0].message.content