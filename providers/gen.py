from config import settings

def _enhance_prompt(messages: list[dict]) -> list[dict]:
    detail_instruction = "\n\nCRITICAL INSTRUCTION: Provide the most exhaustive, comprehensive, and detailed answer possible. Do not summarize or skip any nuances. Elaborate fully on every point."
    
    new_messages = []
    has_system = False
    for msg in messages:
        if msg["role"] == "system":
            new_messages.append({
                "role": "system",
                "content": msg["content"] + detail_instruction
            })
            has_system = True
        else:
            new_messages.append(msg)
            
    if not has_system:
        new_messages.insert(0, {
            "role": "system",
            "content": "You are a highly detailed assistant." + detail_instruction
        })
        
    return new_messages


def generate(messages : list[dict]) -> str:
    messages = _enhance_prompt(messages)

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
    elif settings.gen_provider == "zai":
        return _gen_zai(messages)
    

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
        messages= messages,
        max_tokens=6144
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
            system_instruction=system_instruction,
            max_output_tokens= 6144
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
        messages= messages,
        max_tokens=6144
    )

    return response.choices[0].message.content

def _gen_huggingface(messages: list[dict]) -> str:
    from huggingface_hub import InferenceClient
    
    client = InferenceClient(api_key=settings.hf_api_key, model=settings.gen_model_huggingface)
    
    response = client.chat_completion(
        messages=messages,
        max_tokens=6144
    )
    
    return response.choices[0].message.content

def _gen_zai(messages: list[dict]) -> str:
    from openai import OpenAI
    
    client = OpenAI(
        api_key=settings.zai_api_key,
        base_url="https://api.z.ai/api/paas/v4"
    )

    response = client.chat.completions.create(
        model=settings.gen_model_zai,
        messages=messages,
        max_tokens=6144
    )

    return response.choices[0].message.content